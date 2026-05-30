"""Media helpers: accept any image/video format and produce one clean still.

- `classify`            -> "image" | "video" | None
- `normalize_image`     -> JPEG bytes from any image format (incl. HEIC)
- `extract_video_frame` -> a representative JPEG frame from any video

Both outputs are plain JPEG so the rest of the pipeline (Gemini analysis,
outfit try-on) always works with a single, predictable still image.
"""
from __future__ import annotations

import io
import os
import subprocess
import tempfile

import imageio_ffmpeg
from PIL import Image
from pillow_heif import register_heif_opener

# Lets Pillow open HEIC/HEIF (iPhone) photos like any other image.
register_heif_opener()

# Extensions used as a fallback when the browser sends a generic content type.
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".heic", ".heif"}
_VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v", ".3gp", ".mpeg", ".mpg", ".wmv", ".flv"}


def classify(content_type: str | None, filename: str | None) -> str | None:
    """Return 'image', 'video', or None (unsupported) for an upload."""
    ct = (content_type or "").lower()
    if ct.startswith("image/"):
        return "image"
    if ct.startswith("video/"):
        return "video"

    # Fallback on the file extension (some browsers send octet-stream for HEIC/MKV).
    ext = os.path.splitext(filename or "")[1].lower()
    if ext in _IMAGE_EXTS:
        return "image"
    if ext in _VIDEO_EXTS:
        return "video"
    return None


def normalize_image(data: bytes) -> bytes:
    """Open any supported image and re-encode it as a clean RGB JPEG."""
    with Image.open(io.BytesIO(data)) as img:
        rgb = img.convert("RGB")
        out = io.BytesIO()
        rgb.save(out, format="JPEG", quality=92)
        return out.getvalue()


def extract_video_frame(data: bytes) -> bytes:
    """Grab one representative frame from a video and return it as JPEG bytes.

    Uses the ffmpeg binary bundled with imageio-ffmpeg (no system install needed).
    Tries a smart 'thumbnail' frame first, then falls back to the very first frame.
    """
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    in_path = out_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f_in:
            f_in.write(data)
            in_path = f_in.name
        out_path = in_path + ".jpg"

        attempts = [
            [ffmpeg, "-y", "-i", in_path, "-vf", "thumbnail", "-frames:v", "1", out_path],
            [ffmpeg, "-y", "-i", in_path, "-frames:v", "1", out_path],
        ]
        for cmd in attempts:
            subprocess.run(cmd, capture_output=True, check=False)
            if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                with open(out_path, "rb") as f_out:
                    # Re-normalize through Pillow to guarantee a clean RGB JPEG.
                    return normalize_image(f_out.read())

        raise RuntimeError(
            "Could not read a frame from this video. Try a different file or a photo."
        )
    finally:
        for p in (in_path, out_path):
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
