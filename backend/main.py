"""FastAPI entrypoint for the Vesti AI stylist.

Endpoints:
- POST /api/analyze          -> full StyleBlueprint (fast, one cheap call)
- POST /api/generate-outfit  -> one outfit image, on demand (per outfit clicked)
"""
from __future__ import annotations

import base64
import binascii
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import gemini_service
import media
from gemini_service import GeminiConfigError
from schemas import AnalyzeResponse, GenerateOutfitRequest, GenerateOutfitResponse

app = FastAPI(title="Vesti AI Stylist", version="1.0.0")

# Vite dev server origins. Adjust for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_BYTES = 100 * 1024 * 1024  # 100 MB (videos can be large)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(photo: UploadFile = File(...)) -> AnalyzeResponse:
    """Analyze an uploaded photo or video and return the Style Blueprint.

    Accepts any image or video format. The upload is normalized server-side to a
    single JPEG still (`base_image_b64`) that the frontend reuses for preview and
    outfit generation.
    """
    kind = media.classify(photo.content_type, photo.filename)
    if kind is None:
        raise HTTPException(
            status_code=415,
            detail="Please upload a photo or video (image or video file).",
        )

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

        # Rule: the whole person must be in frame, head to toe.
        if not blueprint.person_fully_visible:
            note = (blueprint.visibility_note or "").strip()
            raise HTTPException(
                status_code=422,
                detail=(
                    "The person cannot be identified fully"
                    + (f" — {note}" if note else "")
                    + ". Please upload a photo showing your full body, head to toe."
                ),
            )

        # Draw the measurement caliper image as part of building the report.
        measurement_image = gemini_service.generate_measurement_image(
            base_image, blueprint.body_measurements
        )
    except GeminiConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - surface a clean message to the UI
        raise HTTPException(status_code=502, detail=f"Analysis failed: {exc}")

    return AnalyzeResponse(
        blueprint=blueprint,
        base_image_b64=base64.b64encode(base_image).decode("ascii"),
        measurement_image_b64=base64.b64encode(measurement_image).decode("ascii"),
    )


@app.post("/api/generate-outfit", response_model=GenerateOutfitResponse)
async def generate_outfit(body: GenerateOutfitRequest) -> GenerateOutfitResponse:
    """Generate one outfit image for the person, on demand."""
    try:
        image_bytes = base64.b64decode(body.image_b64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="image_b64 is not valid base64.")

    if not image_bytes:
        raise HTTPException(status_code=400, detail="image_b64 is empty.")

    try:
        png = gemini_service.generate_outfit_image(image_bytes, body.image_prompt)
    except GeminiConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=502, detail=f"Image generation failed: {exc}")

    return GenerateOutfitResponse(image_b64=base64.b64encode(png).decode("ascii"))


# Serve the built frontend (Vite dist) when present — i.e. inside the Docker image,
# where it is copied to ./static. Mounted last so /api/* and /docs take precedence.
# In local dev there's no ./static, so this is skipped and the backend stays API-only.
_STATIC_DIR = Path(__file__).resolve().parent / "static"
if _STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="spa")
