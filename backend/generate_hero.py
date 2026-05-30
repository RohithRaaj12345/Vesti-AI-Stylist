"""One-off helper: generate the website's hero image with Gemini.

Usage (from the backend venv):
    python generate_hero.py

Reads GEMINI_API_KEY from backend/.env, generates a fashion-editorial hero image
tuned to the site's light + Samsung-blue palette, and saves it to
frontend/public/hero.png. Re-run anytime to regenerate a fresh variation.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai

IMAGE_MODEL = "gemini-2.5-flash-image"

PROMPT = (
    "A high-end fashion editorial portrait of a stylish, confident person in a chic, "
    "well-tailored modern outfit, in a relaxed three-quarter standing pose. Bright, clean "
    "studio background in soft white with subtle blue tones (modern Samsung-style blue, "
    "#1428A0 and #2189FF) and a gentle gradient. Generous negative space, premium "
    "magazine-quality lighting, sharp focus, minimalist and elegant. Color palette: white, "
    "charcoal, and blue accents. Wide composition. No text, no logos, no watermarks."
)

# frontend/public/hero.png, resolved relative to this script (backend/).
OUT_PATH = Path(__file__).resolve().parent.parent / "frontend" / "public" / "hero.png"


def main() -> int:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print(
            "ERROR: GEMINI_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and paste your key from https://aistudio.google.com/apikey",
            file=sys.stderr,
        )
        return 1

    client = genai.Client(api_key=api_key)
    print(f"Generating hero image with {IMAGE_MODEL} …")
    response = client.models.generate_content(model=IMAGE_MODEL, contents=[PROMPT])

    for part in response.parts or []:
        if part.inline_data is not None and part.inline_data.data:
            OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            OUT_PATH.write_bytes(part.inline_data.data)
            print(f"Saved hero image -> {OUT_PATH}")
            return 0

    print("ERROR: Gemini returned no image (possibly blocked). Try re-running.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
