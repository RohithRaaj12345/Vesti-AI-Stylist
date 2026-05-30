"""Pydantic models for the Vesti Style Blueprint.

These models serve a double purpose:
1. They define the JSON shape returned by the `/api/analyze` endpoint.
2. They are passed to Gemini as a `response_schema` so the model returns
   strictly-typed, validated JSON (no fragile string parsing required).
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ColorItem(BaseModel):
    """A single color recommendation with a human name and a hex value."""

    name: str = Field(description="Human-friendly color name, e.g. 'Teal Blue'")
    hex: str = Field(description="Hex code including the leading '#', e.g. '#008080'")


class SilhouetteProfile(BaseModel):
    """Section 1 — Geometric Silhouette Profile (body shape analysis)."""

    body_shape: str = Field(
        description="Detected body shape, e.g. Rectangle, Hourglass, Triangle, Inverted Triangle, Oval"
    )
    shoulder_hip_read: str = Field(
        description="One-line read of the shoulder-to-hip balance"
    )
    torso_length: str = Field(description="Short, balanced, or long torso assessment")
    flattering_silhouettes: list[str] = Field(
        description="3-6 garment silhouettes that flatter this body shape"
    )
    silhouettes_to_avoid: list[str] = Field(
        description="2-4 silhouettes that are less flattering for this body shape"
    )


class FacialArchitecture(BaseModel):
    """Section 2 — Facial Architecture Analysis."""

    face_shape: str = Field(
        description="Detected face shape, e.g. Oval, Round, Square, Heart, Diamond, Oblong"
    )
    recommended_necklines: list[str] = Field(
        description="Necklines that complement this face shape"
    )
    earring_shapes: list[str] = Field(
        description="Earring shapes that complement this face shape"
    )
    eyewear_shapes: list[str] = Field(
        description="Eyewear / glasses frame shapes that complement this face shape"
    )


class ChromaticHarmony(BaseModel):
    """Section 3 — Chromatic Harmony Map (color / undertone analysis)."""

    skin_undertone: str = Field(
        description="Detected skin undertone: Warm, Cool, or Neutral"
    )
    season: str = Field(
        description="Color-analysis 'season', e.g. Warm Autumn, Cool Summer"
    )
    flattering_colors: list[ColorItem] = Field(
        description="Around 10 colors that flatter this person's undertone"
    )
    avoid_colors: list[ColorItem] = Field(
        description="Around 4 colors to avoid for this person's undertone"
    )


class OutfitItem(BaseModel):
    """A single garment / accessory within an outfit, made shoppable."""

    category: str = Field(description="Piece type: 'Top', 'Bottom', 'Footwear', or 'Accessory'")
    description: str = Field(
        description="Human-friendly description, e.g. 'Cream silk relaxed-fit blouse'"
    )
    shopping_query: str = Field(
        description=(
            "Concise retail search keywords for this exact piece (garment type + key "
            "color/material, no filler), e.g. 'cream silk blouse women'. Used to build "
            "a Google Shopping 'Buy' link."
        )
    )


class OutfitFormula(BaseModel):
    """Section 4 — a single complete outfit formula.

    `image_prompt` is reused by the image-generation endpoint to render the
    person wearing this exact look.
    """

    occasion: str = Field(description="Occasion the outfit suits, e.g. 'Smart Casual Office'")
    items: list[OutfitItem] = Field(
        description="The pieces of the outfit: a Top, a Bottom, Footwear, and an Accessory"
    )
    image_prompt: str = Field(
        description=(
            "A single vivid sentence describing the full head-to-toe look, "
            "suitable for an image-generation model to render on the person."
        )
    )


class BodyMeasurements(BaseModel):
    """Approximate, photo-derived body measurements (in centimetres).

    All fields are strings so they can hold honest ranges like '~43-45 cm'.
    Without a reference object these are estimates, not exact values — the
    `body_ratios` (scale-independent) are the most reliable part.
    """

    estimated_height: str = Field(description="Approximate height range in cm, e.g. '~170-175 cm'")
    head: str = Field(description="Approximate head width/circumference in cm")
    shoulder_width: str = Field(description="Approximate shoulder width in cm")
    arm_length: str = Field(description="Approximate arm length in cm")
    hand_length: str = Field(description="Approximate hand length in cm")
    chest: str = Field(description="Approximate chest/bust circumference in cm")
    waist: str = Field(description="Approximate waist circumference in cm")
    hip: str = Field(description="Approximate hip circumference in cm")
    inseam: str = Field(description="Approximate inseam / inner-leg length in cm")
    body_ratios: str = Field(
        description="Scale-independent ratios, e.g. 'shoulder:hip ~1.2:1, head:height ~1:7.5'"
    )
    recommended_top_size: str = Field(description="Suggested top size, e.g. 'M (38)'")
    recommended_bottom_size: str = Field(description="Suggested bottom size, e.g. 'W32'")
    note: str = Field(
        description="Honest disclaimer that these are approximate estimates from a single "
        "photo with no reference scale."
    )


class ConcernZoneSolution(BaseModel):
    """Section 6 — targeted advice for a specific concern zone."""

    zone: str = Field(description="The concern zone, e.g. 'Midsection', 'Arms', 'Height'")
    advice: str = Field(description="Targeted styling advice for this zone")


class StyleBlueprint(BaseModel):
    """Top-level deliverable aggregating all five sections."""

    person_fully_visible: bool = Field(
        description="True only if the WHOLE person is in frame head-to-toe (head, torso, "
        "both arms, legs and feet all visible). False if any part is cut off or out of frame."
    )
    visibility_note: str = Field(
        description="If not fully visible, name the missing parts (e.g. 'legs and feet are "
        "cut off'); otherwise a short confirmation."
    )
    overall_summary: str = Field(
        description="2-3 sentence personal style summary for this person"
    )
    silhouette_profile: SilhouetteProfile
    facial_architecture: FacialArchitecture
    chromatic_harmony: ChromaticHarmony
    body_measurements: BodyMeasurements
    outfit_formulas: list[OutfitFormula] = Field(
        description="16-20 complete outfit formulas across varied occasions"
    )
    concern_zone_solutions: list[ConcernZoneSolution] = Field(
        description="3-6 concern-zone solutions"
    )


class AnalyzeResponse(BaseModel):
    """Response for /api/analyze: the blueprint plus a normalized still image.

    `base_image_b64` is a JPEG (base64, no data-URI prefix) produced server-side
    from whatever was uploaded — a normalized photo, or a frame extracted from a
    video. The frontend uses it for the preview and for outfit generation.
    """

    blueprint: StyleBlueprint
    base_image_b64: str = Field(description="Base64 JPEG still derived from the upload")
    measurement_image_b64: str = Field(
        description="Base64 image of the person with white measurement caliper lines drawn on"
    )


class GenerateOutfitRequest(BaseModel):
    """Request body for the on-demand single-outfit image generation."""

    image_b64: str = Field(description="Base64-encoded original uploaded photo (no data URI prefix)")
    image_prompt: str = Field(description="The outfit's image_prompt from the blueprint")


class GenerateOutfitResponse(BaseModel):
    image_b64: str = Field(description="Base64-encoded generated PNG of the person in the outfit")
