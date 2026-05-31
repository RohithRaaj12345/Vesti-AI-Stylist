# Vesti — API Reference, Workflow & User Flow

Base URL (Docker): `http://127.0.0.1:9005`  ·  API prefix: `/api`  ·  Swagger UI: `/docs`

- All request/response bodies are **JSON** unless noted (`/api/analyze` is `multipart/form-data`).
- **Auth:** after login you receive a **token**. Send it on every protected call as a header:
  `Authorization: Bearer <token>`. The web app stores it in `localStorage`.
- Errors always return `{ "detail": "<human-readable message>" }` with an appropriate HTTP code.

---

## Table of contents
- [Auth endpoints](#auth-endpoints)
  - [Register](#post-apiauthregister)
  - [Verify email](#post-apiauthverify)
  - [Resend code](#post-apiauthresend-otp)
  - [Login](#post-apiauthlogin)
  - [Me](#get-apiauthme)
  - [Logout](#post-apiauthlogout)
- [Styling endpoints](#styling-endpoints)
  - [Health](#get-apihealth)
  - [Analyze](#post-apianalyze)
  - [Generate outfit](#post-apigenerate-outfit)
- [Error codes](#error-codes)
- [Backend workflow](#backend-workflow)
- [User flow](#user-flow)

---

## Auth endpoints

### `POST /api/auth/register`
Create an account and email a 6-digit verification code. **Email must be unique; mobile may repeat.**

**Request**
```json
{
  "name": "Asha R",
  "mobile": "9876543210",
  "email": "asha@example.com",
  "password": "secret12345"
}
```

**Response `200`**
```json
{
  "message": "Registered. Please verify your email.",
  "email": "asha@example.com"
}
```
> In dev mode (SMTP not configured) the response also includes `"dev_email_code": "262610"`.

**Errors:** `400` invalid name/email/mobile/password · `409` email already exists.

```bash
curl -X POST http://127.0.0.1:9005/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Asha R","mobile":"9876543210","email":"asha@example.com","password":"secret12345"}'
```

---

### `POST /api/auth/verify`
Verify the emailed code. (`channel` is optional and defaults to `"email"`.)

**Request**
```json
{ "email": "asha@example.com", "code": "262610" }
```

**Response `200`**
```json
{ "email_verified": true }
```

**Errors:** `400` incorrect/expired code (`{"detail":"Incorrect code."}`) · `404` account not found.

---

### `POST /api/auth/resend-otp`
Re-send a fresh verification code by email.

**Request**
```json
{ "email": "asha@example.com" }
```

**Response `200`**
```json
{ "message": "Code sent." }
```
> Dev mode adds `"dev_code": "884412"`.

---

### `POST /api/auth/login`
Log in. Requires the email to be **verified** first.

**Request**
```json
{ "email": "asha@example.com", "password": "secret12345" }
```

**Response `200`**
```json
{
  "token": "qV8s3mJ2y0n7c1Hk9pX4wZ6tB5aR2dE",
  "name": "Asha R",
  "email": "asha@example.com"
}
```

**Errors:** `401` incorrect email or password · `403` "Please verify your email first."

```bash
curl -X POST http://127.0.0.1:9005/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"asha@example.com","password":"secret12345"}'
```

---

### `GET /api/auth/me`
Return the current user. **Requires** `Authorization: Bearer <token>`.

**Response `200`**
```json
{ "name": "Asha R", "email": "asha@example.com" }
```
**Errors:** `401` not logged in / session expired.

---

### `POST /api/auth/logout`
Invalidate the session (deletes it from Redis). **Requires** the Bearer token.

**Response `200`**
```json
{ "ok": true }
```

---

## Styling endpoints

### `GET /api/health`
Liveness check (no auth).

**Response `200`** → `{ "status": "ok" }`

---

### `POST /api/analyze`
Upload a **photo or video** → full style blueprint **+** a normalized still **+** the
measurement-overlay image. **Requires** the Bearer token. **Rate limited to 1 success per
user per 30 minutes.**

**Request:** `multipart/form-data` with a single field `photo` (any image/video, ≤ 100 MB).

```bash
curl -X POST http://127.0.0.1:9005/api/analyze \
  -H "Authorization: Bearer <token>" \
  -F "photo=@/path/to/full-body.jpg"
```

**Response `200`** (base64 fields truncated for readability)
```json
{
  "blueprint": {
    "person_fully_visible": true,
    "visibility_note": "Full body visible, head to toe.",
    "overall_summary": "A balanced rectangle silhouette with cool undertones; clean tailored lines suit you best.",
    "silhouette_profile": {
      "body_shape": "Rectangle",
      "shoulder_hip_read": "Shoulders and hips are well balanced.",
      "torso_length": "Balanced",
      "flattering_silhouettes": ["Structured blazers", "Belted dresses", "Straight-leg trousers"],
      "silhouettes_to_avoid": ["Boxy oversized tops"]
    },
    "facial_architecture": {
      "face_shape": "Oval",
      "recommended_necklines": ["V-neck", "Scoop"],
      "earring_shapes": ["Studs", "Small hoops"],
      "eyewear_shapes": ["Rectangular", "Cat-eye"]
    },
    "chromatic_harmony": {
      "skin_undertone": "Cool",
      "season": "Cool Summer",
      "flattering_colors": [
        { "name": "Teal Blue", "hex": "#008080" },
        { "name": "Soft Rose", "hex": "#C5828B" }
      ],
      "avoid_colors": [
        { "name": "Bright Orange", "hex": "#FF7A00" }
      ]
    },
    "body_measurements": {
      "estimated_height": "~165-170 cm",
      "head": "~21-22 cm",
      "shoulder_width": "~40-42 cm",
      "arm_length": "~55-58 cm",
      "hand_length": "~18-19 cm",
      "chest": "~88-92 cm",
      "waist": "~72-76 cm",
      "hip": "~94-98 cm",
      "inseam": "~74-78 cm",
      "body_ratios": "shoulder:hip ~1:1, head:height ~1:7.8, torso:leg ~1:1.1",
      "recommended_top_size": "M",
      "recommended_bottom_size": "W30",
      "note": "Approximate estimates read from a single photo with no reference scale."
    },
    "outfit_formulas": [
      {
        "occasion": "Smart Casual Office",
        "items": [
          { "category": "Top", "description": "Cream silk blouse", "shopping_query": "cream silk blouse women" },
          { "category": "Bottom", "description": "Navy tailored trousers", "shopping_query": "navy tailored trousers women" },
          { "category": "Footwear", "description": "Tan leather loafers", "shopping_query": "tan leather loafers women" },
          { "category": "Accessory", "description": "Gold chain belt", "shopping_query": "gold chain belt" }
        ],
        "image_prompt": "Cream silk blouse, navy tailored trousers, tan loafers and a thin gold belt."
      }
    ],
    "concern_zone_solutions": [
      { "zone": "Midsection", "advice": "Use semi-tucked tops and structured fabrics to define the waist." }
    ]
  },
  "base_image_b64": "/9j/4AAQSkZJRgABAQ...(truncated)",
  "measurement_image_b64": "/9j/4AAQSkZJRgABAQ...(truncated)"
}
```
> `outfit_formulas` contains **16–20** items (one shown above).
> `base_image_b64` = normalized JPEG of the upload (for preview + try-on).
> `measurement_image_b64` = the photo with the white measurement overlay drawn on it.

**Errors:** `401` not logged in · `403`/`422` "person cannot be identified fully" (not full
body) · `413` file > 100 MB · `415` not an image/video · `429` rate limited (see below) ·
`502` Gemini failure.

**`429` example**
```json
{ "detail": "You can upload once every 30 minutes. Please try again in about 30 minute(s)." }
```

---

### `POST /api/generate-outfit`
Render the **same person** wearing one outfit (frame-locked to the upload). **Requires** the
Bearer token. Send the `base_image_b64` from `/api/analyze` and the outfit's `image_prompt`.

**Request**
```json
{
  "image_b64": "/9j/4AAQSkZJRgABAQ...(the base_image_b64 from analyze)",
  "image_prompt": "Cream silk blouse, navy tailored trousers, tan loafers and a thin gold belt."
}
```

**Response `200`**
```json
{ "image_b64": "iVBORw0KGgoAAAANSUhEUg...(truncated PNG/JPEG)" }
```

**Errors:** `400` invalid base64 · `401` not logged in · `502` generation failed.

---

## Error codes

| Code | Meaning |
|------|---------|
| 400 | Bad input (validation, empty file, invalid base64) |
| 401 | Not logged in / session expired (bad or missing Bearer token) |
| 403 | Email not verified (login) / person not fully visible (analyze) |
| 409 | Email already registered |
| 413 | Upload larger than 100 MB |
| 415 | Unsupported file (not an image or video) |
| 422 | Person not fully in frame (alias of the full-body block) |
| 429 | Upload rate limit hit (1 per 30 min per user) |
| 500 | Server/config error (e.g. missing GEMINI_API_KEY) |
| 502 | Gemini call failed (quota, safety block, etc.) |

---

## Backend workflow

**Register → verify → login**
1. `register`: validate name/email/mobile/password (`validators.py`) → insert `users` row
   (bcrypt password hash, UUID id) → create a 6-digit code, store its **hash** in the `otps`
   table (`otp.py`) → email it via SMTP, or log it in dev (`notify.py`) → log to MySQL + file.
2. `verify`: match the latest unconsumed/unexpired code for the user → set `email_verified`.
3. `login`: check password **and** `email_verified` → create a random session token in
   **Redis** (`sess:<token>` → user, 7-day TTL) → return the token.
4. Protected calls resolve `Authorization: Bearer <token>` → Redis → the `User`
   (`auth.current_user`), else `401`.

**Analyze (`/api/analyze`)**
1. Auth (Bearer → Redis → user).
2. **Rate-limit check** — if Redis `upload:<user_id>` exists → `429` (quota *not* consumed on
   failures).
3. Classify the upload (`media.classify`): image → normalize to JPEG; video → extract a frame
   **and** send the clip to Gemini's Files API.
4. **Analyze** with `gemini-2.5-flash` (low temperature) → validated `StyleBlueprint`
   (`response_schema`). If `person_fully_visible` is false → `403/422`.
5. **Measurement overlay** with `gemini-2.5-flash-image` (`generate_measurement_image`),
   frame-locked to the upload.
6. On success → `ratelimit.mark(user.id)` (start the 30-min window) → log the action + cost →
   return `{ blueprint, base_image_b64, measurement_image_b64 }`.

**Generate outfit (`/api/generate-outfit`)**
1. Auth. 2. Decode `image_b64`. 3. `gemini-2.5-flash-image` restyles only the clothing,
   frame-locked. 4. Log action + cost → return the image.

**Storage**
- **MySQL** — `users`, `otps`, `request_logs` (all UUID keys; the audit log records who/when/
  model/₹ cost).
- **Redis** — `sess:<token>` (sessions), `upload:<user_id>` (30-min rate-limit key).

---

## User flow

1. **Land on the site** → the app checks `localStorage` for a token (`GET /api/auth/me`). If
   not logged in, the tool area shows the **Login / Register** card.
2. **Register** — enter name, mobile, email, password → a 6-digit code is **emailed**.
3. **Verify** — enter the email code → email verified.
4. **Log in** — email + password → token saved to `localStorage`; the uploader appears, the
   nav shows the email + **Log out**.
5. **Upload** a full-body photo or video → after a few seconds the **report** appears:
   style summary, shape & features, color palette, the **measurement overlay image**, 16–20
   outfit cards, and concern-zone tips. *(Limited to 1 upload per 30 minutes.)*
6. **Shop** — each outfit item has a **🛒 Buy** link (Google Shopping search).
7. **Visualize** — click **✨ Generate look** on an outfit to see yourself wearing it (same
   frame, only clothing changes).
8. **Log out** — clears the token and the Redis session.

---

*Models in use: `gemini-2.5-flash` (analysis), `gemini-2.5-flash-image` (measurement overlay +
outfit try-on). Approx cost: ~₹4.5 per analysis, ~₹3.7 per outfit image.*
