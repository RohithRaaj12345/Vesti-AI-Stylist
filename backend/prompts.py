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
4. Body Measurements — measure the person as they actually are. There is NO
   reference object, so you cannot be exact: estimate the person's overall height
   range from their visible proportions, then scale every other measurement from
   it. Express each as an APPROXIMATE RANGE in centimetres, e.g. "~43-45 cm".
   Provide: estimated_height, head (width/circumference), shoulder_width,
   arm_length, hand_length, chest, waist, hip, inseam. Also give `body_ratios`
   that do NOT depend on absolute scale (e.g. "shoulder:hip ~1.2:1, head:height
   ~1:7.5, torso:leg ~1:1.1") — these are the most reliable numbers. Give
   recommended_top_size and recommended_bottom_size. Keep `note` honest: state that
   these are approximate estimates read from a single photo with no reference scale.
   Never invent confident exact numbers; ranges only.
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
    """Instruct the image model to add a geometric body-proportion overlay.

    Matches a stylist's body-frame map: centre axes, shoulder/hip corner brackets,
    diagonal hourglass lines and a centre diamond — plus measurement labels.
    `measures` supplies the EXACT label text so the model never invents numbers.
    """
    return (
        "Add a clean GEOMETRIC BODY-PROPORTION overlay on top of this photo, in the "
        "minimalist style of a stylist's body-frame map. Keep this SIMPLE and CLEAR.\n\n"
        "ABSOLUTE RULES:\n"
        "- Keep the underlying photo EXACTLY the same: same person, face, hair, body, "
        "clothing, pose, background, framing and dimensions. Only add overlay lines on top.\n"
        "- Use ONE single colour for every line and label: solid bright WHITE.\n"
        "- Lines must be BOLD, perfectly STRAIGHT, clean and sharp — easy to see. Keep the "
        "number of lines small so it stays uncluttered.\n\n"
        "Draw exactly these elements, aligned to the body:\n"
        "- A vertical CENTRE line straight down the middle, from the top of the head to "
        "between the feet.\n"
        "- A horizontal line across the waist, spanning the body width.\n"
        "- Right-angle corner BRACKETS at the two SHOULDERS marking shoulder width.\n"
        "- Right-angle corner BRACKETS at the two HIPS marking hip width.\n"
        "- A small DIAMOND outline at the centre of the waist.\n\n"
        "Add LARGE, clearly readable WHITE labels beside the matching lines, using EXACTLY "
        "this text (keep labels off the body, in the empty space):\n"
        f"- Height: {measures.estimated_height}\n"
        f"- Shoulders: {measures.shoulder_width}\n"
        f"- Waist: {measures.waist}\n"
        f"- Hips: {measures.hip}\n\n"
        "Result: a simple, bold, clean WHITE measurement overlay that is easy to read, on "
        "the completely unchanged photo."
    )
