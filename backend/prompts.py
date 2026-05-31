"""Prompt templates for the analysis and image-generation Gemini calls."""

ANALYSIS_PROMPT = """\
You are Vesti, an expert personal stylist, color analyst and fit advisor. Analyze
the person in the provided photo or video and produce a complete, personalized
Style Blueprint for this person EXACTLY AS THEY ARE.

Ground rules (very important):
- Describe the person exactly as they appear. Do NOT slim, flatter, idealize or
  alter their body, proportions, or features in any way.
- Base every statement strictly on what is visible. Prioritise accuracy over
  flattery, and never contradict the photo.
- If something is not clearly visible, say "not clearly visible" instead of guessing.
(If you are given a video, use the clearest full-body frames across the footage.)

FIRST, check full-body visibility. Set `person_fully_visible` to true ONLY if the
entire person is in frame head-to-toe — head, torso, both arms, legs and feet all
visible. If any of those is cut off, out of frame, or hidden, set it to false and
in `visibility_note` say which parts are missing. (Still fill the rest of the
schema as best you can.)

Produce ALL of the following, filling every field of the schema:

1. Geometric Silhouette Profile — read the body shape, shoulder-to-hip balance and
   torso length, then list garment silhouettes that flatter, and a few to avoid.
2. Facial Architecture Analysis — read the face shape and recommend complementary
   necklines, earring shapes and eyewear shapes.
3. Chromatic Harmony Map — determine the skin undertone and color "season", then
   give about 10 flattering colors and about 4 colors to avoid. Every color MUST
   include a realistic hex code.
4. Body Measurements — estimate the person's sizes as they actually are, in
   centimetres. Method (IMPORTANT for consistency):
   a) First decide the person's clothing sizes confidently from the photo:
      `recommended_top_size` (e.g. S/M/L or a chest number) and
      `recommended_bottom_size` (a waist size, e.g. W30).
   b) Then DERIVE the body WIDTH measurements from those sizes using standard adult
      size charts, so the numbers AGREE with the sizes — they must not contradict:
      - `waist` (cm) must match the bottom/waist size (e.g. W30 ≈ 76 cm, W32 ≈ 81 cm).
      - `chest` must match the top size (e.g. men's M ≈ 96-101 cm, women's M ≈ 88-92 cm).
      - `hip` ≈ a few cm more than the waist; `shoulder_width` follows from the top size.
   c) Estimate `estimated_height`, `inseam`, `head`, `arm_length`, `hand_length`
      from the visible body proportions.
   Express every value as an APPROXIMATE RANGE, e.g. "~75-80 cm". Also give
   `body_ratios` (scale-independent, e.g. "shoulder:hip ~1.2:1, head:height ~1:7.5").
   Keep `note` honest: approximate estimates from a single photo, no reference scale.
   The widths and the recommended sizes must be mutually consistent.
5. Outfit Formulas — design 16 to 20 complete, varied head-to-toe outfits across
   different occasions (work, casual, evening, formal, weekend, travel, etc.).
   Express each outfit as an `items` list of about 4 pieces — a Top, a Bottom,
   Footwear, and an Accessory. For every piece give its `category`, a friendly
   `description`, and a concise `shopping_query`: short, retail-style search
   keywords (garment type plus key color/material, no filler words), e.g.
   "cream silk blouse women" or "tan leather loafers". Also write a single vivid
   `image_prompt` sentence describing the whole look so it can later be rendered
   on this exact person.
6. Concern Zone Solutions — give 3 to 6 targeted tips for common concern zones.

Return ONLY the structured data defined by the response schema.
"""


def build_image_prompt(outfit_image_prompt: str) -> str:
    """Strict virtual try-on instruction: change ONLY the clothing.

    The user's own photo is passed alongside this text. The goal is to keep the
    person completely unchanged and only swap their garments.
    """
    return (
        "This is a virtual clothing try-on. Take the EXACT person in the provided "
        "image and change ONLY their clothing to the following outfit: "
        f"{outfit_image_prompt}. "
        "Keep absolutely everything else identical to the original image: the same "
        "face, the same hair and hairstyle, the same body size and exact body "
        "proportions, the same skin tone, the same pose, the same camera framing and "
        "crop, the same lighting, and the same background. "
        "Do NOT resize, slim, stretch or reshape the body. Do NOT change the "
        "hairstyle, face, pose or background. Only the garments may change. "
        "Keep the EXACT same frame, aspect ratio, crop and image dimensions as the input. "
        "Photorealistic, with the new clothing fitted naturally to the person's real body."
    )


def build_measurement_prompt(measures) -> str:
    """Instruct the image model to add an elegant geometric body-proportion overlay.

    Reproduces the iconik body-frame map: thin grey axes, shoulder/hip corner
    brackets, dotted diagonal hourglass lines and a centre diamond — NO text.
    `measures` is unused (the overlay is purely geometric; sizes show in the caption).
    """
    return (
        "Add an ELEGANT GEOMETRIC body-proportion overlay on top of this photo, in the refined "
        "minimalist style of a fashion stylist's body-frame analysis (like a Da Vinci "
        "proportion study). Keep the underlying photo EXACTLY the same (same person, face, "
        "body, clothing, pose, background, framing and dimensions) — only add the thin overlay "
        "on top.\n\n"
        "STYLE: use THIN, elegant, semi-transparent soft WHITE / light GREY lines — subtle and "
        "refined, NOT bold. Absolutely NO text, NO numbers, NO labels anywhere on the image.\n\n"
        "Draw, anchored symmetrically and precisely to the body:\n"
        "1. A vertical CENTRE AXIS line straight down the body's midline — through the centre "
        "of the head, the navel, and down to between the feet.\n"
        "2. A horizontal AXIS line crossing it at chest/shoulder level, extending a little "
        "beyond the body on both sides.\n"
        "3. Small right-angle CORNER BRACKETS marking the SHOULDER width (upper, at the two "
        "shoulders) and the HIP width (lower, at the two hips).\n"
        "4. Two faint DOTTED diagonal lines running from the shoulders downward and outward "
        "past the hips, crossing at the body centre to form an hourglass / X.\n"
        "5. A small DIAMOND (rhombus) outline at the centre where the lines cross (navel level).\n\n"
        "The result must look elegant, symmetrical, minimal and precise — thin grey geometric "
        "lines only, NO text or numbers, on the completely unchanged photo."
    )
