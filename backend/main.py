"""FastAPI entrypoint for the Vesti AI stylist.

Auth (MySQL + Redis), per-user upload rate limiting, logging, and the styling endpoints.
"""
from __future__ import annotations

import base64
import binascii
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import auth
import db
import gemini_service
import logs
import media
import notify
import otp
import ratelimit
import validators
from db import SessionLocal, User
from gemini_service import GeminiConfigError
from schemas import AnalyzeResponse, GenerateOutfitRequest, GenerateOutfitResponse

app = FastAPI(title="Vesti AI Stylist", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],  # includes Authorization
)

MAX_BYTES = 100 * 1024 * 1024  # 100 MB (videos can be large)


@app.on_event("startup")
def _startup() -> None:
    logs.logger.info("Starting Vesti; connecting to MySQL...")
    db.init_db()
    logs.logger.info("MySQL ready; OTP dev mode = %s", notify.DEV_MODE)


def client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else ""


# --------------------------------------------------------------------------- auth

class RegisterIn(BaseModel):
    name: str
    email: str
    mobile: str
    password: str


class VerifyIn(BaseModel):
    email: str
    code: str
    channel: str = "email"  # kept for compatibility; only email is used


class ResendIn(BaseModel):
    email: str
    channel: str = "email"


class LoginIn(BaseModel):
    email: str
    password: str


@app.post("/api/auth/register")
def register(body: RegisterIn, request: Request) -> dict:
    ip = client_ip(request)
    try:
        name = validators.clean_name(body.name)
        email = validators.clean_email(body.email)
        mobile = validators.clean_mobile(body.mobile)
        password = validators.clean_password(body.password)
    except validators.ValidationError as exc:
        logs.log_event(action="register", status="error", ip=ip, detail=str(exc))
        raise HTTPException(status_code=400, detail=str(exc))

    with SessionLocal() as s:
        exists = s.query(User).filter(User.email == email).first()
        if exists:
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists.",
            )
        user = User(
            name=name, email=email, mobile=mobile,
            password_hash=auth.hash_password(password),
        )
        s.add(user)
        s.commit()
        email_code = otp.issue_otp(s, user, "email")
        logs.log_event(action="register", status="ok", user=user, ip=ip)
        resp = {
            "message": "Registered. Please verify your email.",
            "email": user.email,
        }
        # Surface the code only when SMTP isn't configured (pure dev fallback).
        if notify.DEV_MODE and not notify.smtp_enabled():
            resp["dev_email_code"] = email_code
        return resp


@app.post("/api/auth/verify")
def verify(body: VerifyIn, request: Request) -> dict:
    ip = client_ip(request)
    email = (body.email or "").strip().lower()
    with SessionLocal() as s:
        user = s.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=404, detail="Account not found.")
        try:
            otp.verify_otp(s, user, "email", body.code)
        except otp.OtpError as exc:
            logs.log_event(action="verify", status="error", user=user, ip=ip, detail=str(exc))
            raise HTTPException(status_code=400, detail=str(exc))
        logs.log_event(action="verify", status="ok", user=user, ip=ip, detail="email")
        return {"email_verified": user.email_verified}


@app.post("/api/auth/resend-otp")
def resend_otp(body: ResendIn) -> dict:
    email = (body.email or "").strip().lower()
    with SessionLocal() as s:
        user = s.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=404, detail="Account not found.")
        code = otp.issue_otp(s, user, "email")
        resp = {"message": "Code sent."}
        if notify.DEV_MODE and not notify.smtp_enabled():
            resp["dev_code"] = code
        return resp


@app.post("/api/auth/login")
def login(body: LoginIn, request: Request) -> dict:
    ip = client_ip(request)
    email = (body.email or "").strip().lower()
    with SessionLocal() as s:
        user = s.query(User).filter(User.email == email).first()
        if user is None or not auth.verify_password(body.password, user.password_hash):
            logs.log_event(action="login", status="error", user=user, ip=ip,
                           detail="bad credentials")
            raise HTTPException(status_code=401, detail="Incorrect email or password.")
        if not user.email_verified:
            logs.log_event(action="login", status="blocked", user=user, ip=ip,
                           detail="email unverified")
            raise HTTPException(
                status_code=403,
                detail="Please verify your email first.",
            )
        token = auth.create_session(user)
        logs.log_event(action="login", status="ok", user=user, ip=ip)
        return {"token": token, "name": user.name, "email": user.email}


@app.post("/api/auth/logout")
def logout(authorization: str | None = Header(default=None)) -> dict:
    auth.destroy_session(auth.token_from_header(authorization))
    return {"ok": True}


@app.get("/api/auth/me")
def me(user: User = Depends(auth.current_user)) -> dict:
    return {"name": user.name, "email": user.email}


# ------------------------------------------------------------------------- styling

@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: Request,
    photo: UploadFile = File(...),
    user: User = Depends(auth.current_user),
) -> AnalyzeResponse:
    """Analyze an uploaded photo/video → Style Blueprint + measurement overlay image."""
    ip = client_ip(request)

    # Per-user rate limit (quota is consumed only on success, below).
    wait = ratelimit.seconds_until_allowed(user.id)
    if wait > 0:
        mins = max(1, (wait + 59) // 60)
        logs.log_event(action="analyze", status="blocked", user=user, ip=ip,
                       detail=f"rate limited, {wait}s left")
        raise HTTPException(
            status_code=429,
            detail=f"You can upload once every {ratelimit.WINDOW_MIN} minutes. "
                   f"Please try again in about {mins} minute(s).",
        )

    kind = media.classify(photo.content_type, photo.filename)
    if kind is None:
        logs.log_event(action="analyze", status="error", user=user, ip=ip,
                       detail="unsupported file")
        raise HTTPException(status_code=415, detail="Please upload a photo or video.")

    data = await photo.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File must be 100 MB or smaller.")

    try:
        if kind == "video":
            base_image = media.extract_video_frame(data)
            blueprint = gemini_service.analyze_video(data)
        else:
            base_image = media.normalize_image(data)
            blueprint = gemini_service.analyze_image_bytes(base_image)

        if not blueprint.person_fully_visible:
            note = (blueprint.visibility_note or "").strip()
            raise HTTPException(
                status_code=422,
                detail="The person cannot be identified fully"
                + (f" — {note}" if note else "")
                + ". Please upload a photo showing your full body, head to toe.",
            )

        measurement_image = gemini_service.generate_measurement_image(
            base_image, blueprint.body_measurements
        )
    except HTTPException as exc:
        status = "blocked" if exc.status_code == 422 else "error"
        logs.log_event(action="analyze", status=status, user=user, ip=ip,
                       kind=kind, detail=str(exc.detail))
        raise
    except GeminiConfigError as exc:
        logs.log_event(action="analyze", status="error", user=user, ip=ip, detail=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        logs.log_event(action="analyze", status="error", user=user, ip=ip, detail=str(exc))
        raise HTTPException(status_code=502, detail=f"Analysis failed: {exc}")

    ratelimit.mark(user.id)  # consume the 30-min quota now that it succeeded
    cost = logs.estimate_cost(gemini_service.ANALYSIS_MODEL) + logs.estimate_cost(
        gemini_service.MEASUREMENT_MODELS[0]
    )
    logs.log_event(action="analyze", status="ok", user=user, ip=ip, kind=kind,
                   model=gemini_service.MEASUREMENT_MODELS[0],
                   detail="report+measurement", cost_inr=cost)

    return AnalyzeResponse(
        blueprint=blueprint,
        base_image_b64=base64.b64encode(base_image).decode("ascii"),
        measurement_image_b64=base64.b64encode(measurement_image).decode("ascii"),
    )


@app.post("/api/generate-outfit", response_model=GenerateOutfitResponse)
async def generate_outfit(
    request: Request,
    body: GenerateOutfitRequest,
    user: User = Depends(auth.current_user),
) -> GenerateOutfitResponse:
    """Generate one outfit image for the person, on demand."""
    ip = client_ip(request)
    try:
        image_bytes = base64.b64decode(body.image_b64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="image_b64 is not valid base64.")
    if not image_bytes:
        raise HTTPException(status_code=400, detail="image_b64 is empty.")

    try:
        png = gemini_service.generate_outfit_image(image_bytes, body.image_prompt)
    except GeminiConfigError as exc:
        logs.log_event(action="generate_outfit", status="error", user=user, ip=ip, detail=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        logs.log_event(action="generate_outfit", status="error", user=user, ip=ip, detail=str(exc))
        raise HTTPException(status_code=502, detail=f"Image generation failed: {exc}")

    logs.log_event(action="generate_outfit", status="ok", user=user, ip=ip,
                   model=gemini_service.IMAGE_MODEL,
                   cost_inr=logs.estimate_cost(gemini_service.IMAGE_MODEL))
    return GenerateOutfitResponse(image_b64=base64.b64encode(png).decode("ascii"))


# Serve the built frontend (Vite dist) when present (inside the Docker image -> ./static).
# Mounted last so /api/* and /docs take precedence. Skipped in local API-only dev.
_STATIC_DIR = Path(__file__).resolve().parent / "static"
if _STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="spa")
