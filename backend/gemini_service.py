"""Thin wrapper around the Gemini (google-genai) SDK.

Two capabilities:
- `analyze_image`  -> structured StyleBlueprint via gemini-2.5-flash
- `generate_outfit_image` -> a restyled photo via gemini-2.5-flash-image
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from google import genai
from google.genai import types

import prompts
from schemas import StyleBlueprint

load_dotenv()

ANALYSIS_MODEL = "gemini-2.5-flash"
IMAGE_MODEL = "gemini-2.5-flash-image"


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


def analyze_image(image_bytes: bytes, mime_type: str) -> StyleBlueprint:
    """Run the multimodal analysis and return a validated StyleBlueprint."""
    response = _client().models.generate_content(
        model=ANALYSIS_MODEL,
        contents=[
            prompts.ANALYSIS_PROMPT,
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=StyleBlueprint,
        ),
    )
    blueprint = response.parsed
    if blueprint is None:
        # Safety filters or a malformed response can yield no parsed object.
        raise RuntimeError(
            "Gemini did not return a usable analysis. Try a clearer, full-body photo."
        )
    return blueprint


def generate_outfit_image(
    image_bytes: bytes, mime_type: str, outfit_image_prompt: str
) -> bytes:
    """Render the SAME person wearing the described outfit; return PNG bytes."""
    response = _client().models.generate_content(
        model=IMAGE_MODEL,
        contents=[
            prompts.build_image_prompt(outfit_image_prompt),
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
    )

    for part in response.parts or []:
        if part.inline_data is not None and part.inline_data.data:
            return part.inline_data.data

    raise RuntimeError(
        "Gemini returned no image (the request may have been blocked). "
        "Try a different outfit or photo."
    )
