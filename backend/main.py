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
from gemini_service import GeminiConfigError
from schemas import GenerateOutfitRequest, GenerateOutfitResponse, StyleBlueprint

app = FastAPI(title="Vesti AI Stylist", version="1.0.0")

# Vite dev server origins. Adjust for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=StyleBlueprint)
async def analyze(photo: UploadFile = File(...)) -> StyleBlueprint:
    """Analyze an uploaded person photo and return the full Style Blueprint."""
    if photo.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Please upload a JPEG, PNG or WebP image.",
        )

    data = await photo.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller.")

    try:
        return gemini_service.analyze_image(data, photo.content_type)
    except GeminiConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:  # pragma: no cover - surface a clean message to the UI
        raise HTTPException(status_code=502, detail=f"Analysis failed: {exc}")


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
        png = gemini_service.generate_outfit_image(
            image_bytes, "image/png", body.image_prompt
        )
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
