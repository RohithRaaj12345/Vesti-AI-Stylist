"""Thin wrapper around the Gemini (google-genai) SDK.

Two capabilities:
- `analyze_image`  -> structured StyleBlueprint via gemini-2.5-flash
- `generate_outfit_image` -> a restyled photo via gemini-2.5-flash-image
"""
from __future__ import annotations

import io
import os
import tempfile
import time
from functools import lru_cache

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

import prompts
from schemas import StyleBlueprint

load_dotenv()

ANALYSIS_MODEL = "gemini-2.5-flash"
IMAGE_MODEL = "gemini-2.5-flash-image"
# Measurement overlay: Gemini 3 Pro (best placement/text); flash only as a fallback.
MEASUREMENT_MODELS = ["gemini-3-pro-image", "gemini-2.5-flash-image"]


def _analysis_config() -> types.GenerateContentConfig:
    """Shared config for the analysis call: strict JSON + low temperature."""
    return types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=StyleBlueprint,
        temperature=0.2,  # lower -> more grounded, less hallucination
    )


def _parsed_or_raise(response) -> StyleBlueprint:
    blueprint = response.parsed
    if blueprint is None:
        raise RuntimeError(
            "Gemini did not return a usable analysis. Try a clearer, full-body shot."
        )
    return blueprint


class GeminiConfigError(RuntimeError):
    """Raised when the API key is missing or the client cannot be created."""


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    """Create (once) and return the shared Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        raise GeminiConfigError(
            "GEMINI_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and paste your key from https://aistudio.google.com/apikey"
        )
    return genai.Client(api_key=api_key)


def analyze_image_bytes(jpeg_bytes: bytes) -> StyleBlueprint:
    """Analyze a normalized JPEG still and return a validated StyleBlueprint."""
    response = _client().models.generate_content(
        model=ANALYSIS_MODEL,
        contents=[
            prompts.ANALYSIS_PROMPT,
            types.Part.from_bytes(data=jpeg_bytes, mime_type="image/jpeg"),
        ],
        config=_analysis_config(),
    )
    return _parsed_or_raise(response)


def analyze_video(video_bytes: bytes) -> StyleBlueprint:
    """Analyze a full video via the Files API and return a StyleBlueprint.

    Uploads the clip, waits for it to finish processing, runs the analysis (Gemini
    samples multiple frames), then deletes the uploaded file.
    """
    client = _client()
    tmp_path = None
    uploaded = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(video_bytes)
            tmp_path = f.name

        uploaded = client.files.upload(file=tmp_path)

        # Wait for server-side processing (up to ~60s) before using the file.
        waited = 0.0
        while getattr(uploaded.state, "name", "") == "PROCESSING" and waited < 60:
            time.sleep(2)
            waited += 2
            uploaded = client.files.get(name=uploaded.name)
        if getattr(uploaded.state, "name", "") == "FAILED":
            raise RuntimeError("The video could not be processed. Try a different file.")

        response = client.models.generate_content(
            model=ANALYSIS_MODEL,
            contents=[prompts.ANALYSIS_PROMPT, uploaded],
            config=_analysis_config(),
        )
        return _parsed_or_raise(response)
    finally:
        if uploaded is not None:
            try:
                client.files.delete(name=uploaded.name)
            except Exception:
                pass
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def _sniff_mime(image_bytes: bytes) -> str:
    """Best-effort image mime from magic bytes (defaults to JPEG)."""
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _match_frame(generated: bytes, width: int, height: int) -> bytes:
    """Force a generated image to the exact frame (aspect + size) of the input.

    Center-crops to the target aspect ratio if needed, then resizes to (width, height).
    """
    with Image.open(io.BytesIO(generated)) as img:
        img = img.convert("RGB")
        gw, gh = img.size
        target = width / height
        current = gw / gh
        if abs(current - target) > 0.01:
            if current > target:  # too wide -> crop sides
                new_w = int(round(gh * target))
                left = (gw - new_w) // 2
                img = img.crop((left, 0, left + new_w, gh))
            else:  # too tall -> crop top/bottom
                new_h = int(round(gw / target))
                top = (gh - new_h) // 2
                img = img.crop((0, top, gw, top + new_h))
        img = img.resize((width, height), Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=92)
        return out.getvalue()


def _first_image_part(response) -> bytes:
    for part in response.parts or []:
        if part.inline_data is not None and part.inline_data.data:
            return part.inline_data.data
    raise RuntimeError(
        "Gemini returned no image (the request may have been blocked). "
        "Try a different photo."
    )


def _input_size(image_bytes: bytes) -> tuple[int, int]:
    with Image.open(io.BytesIO(image_bytes)) as img:
        return img.size


def generate_outfit_image(image_bytes: bytes, outfit_image_prompt: str) -> bytes:
    """Render the SAME person wearing the described outfit, in the same frame."""
    w, h = _input_size(image_bytes)
    response = _client().models.generate_content(
        model=IMAGE_MODEL,
        contents=[
            prompts.build_image_prompt(outfit_image_prompt),
            types.Part.from_bytes(data=image_bytes, mime_type=_sniff_mime(image_bytes)),
        ],
    )
    return _match_frame(_first_image_part(response), w, h)


def generate_measurement_image(image_bytes, measures) -> bytes:
    """Add a clean single-color measurement overlay; keep the same frame.

    Tries the strongest image model first and falls back to others if a model
    isn't enabled on the key.
    """
    w, h = _input_size(image_bytes)
    prompt = prompts.build_measurement_prompt(measures)
    part = types.Part.from_bytes(data=image_bytes, mime_type=_sniff_mime(image_bytes))

    last_error: Exception | None = None
    for model in MEASUREMENT_MODELS:
        try:
            response = _client().models.generate_content(
                model=model, contents=[prompt, part]
            )
            return _match_frame(_first_image_part(response), w, h)
        except Exception as exc:  # model not available / blocked -> try the next
            last_error = exc
            continue

    raise RuntimeError(
        f"Could not generate the measurement image: {last_error}"
    )
