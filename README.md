# Vesti — AI Personal Stylist

Upload one full-body photo of a person → get a complete AI **Style Blueprint**
(body shape, face analysis, color palette, 16–20 shoppable outfit formulas, and
concern-zone tips) and **generate a photo of that same person wearing any outfit**,
on demand.

Inspired by [iconik.pro](https://www.iconik.pro/). Fully automated — no human
stylist, no consultation call. Powered by **Google Gemini** (vision analysis +
image generation).

---

## Table of contents
- [Features](#features)
- [Tech stack](#tech-stack)
- [How it works](#how-it-works)
- [Architecture](#architecture)
- [Project layout](#project-layout)
- [Prerequisites](#prerequisites)
- [Setup & run](#setup--run)
- [API reference](#api-reference)
- [Style Blueprint data structure](#style-blueprint-data-structure)
- [Configuration](#configuration)
- [Cost](#cost)
- [Troubleshooting](#troubleshooting)
- [Limitations & roadmap](#limitations--roadmap)

---

## Features

- **One-photo analysis** — upload a single full-body photo; Gemini Vision reads body
  shape, face shape, skin undertone and proportions.
- **Full Style Blueprint** — five sections: Silhouette Profile, Facial Architecture,
  Chromatic Harmony (color palette), 16–20 Outfit Formulas, and Concern-Zone Solutions.
- **Shoppable outfits** — every garment (Top, Bottom, Footwear, Accessory) has a
  **🛒 Buy** link that opens a Google Shopping search for that item, so customers go
  straight from suggestion to purchase.
- **On-demand "Generate look"** — render the *same person* wearing any suggested
  outfit. Images are generated one at a time, only for the looks the user picks
  (you pay only for what's generated).
- **Structured, validated output** — Gemini returns strictly-typed JSON via a Pydantic
  `response_schema`, so there's no fragile text parsing.
- **Samsung-style UI** — clean light theme with a sticky nav, full-width hero,
  "how it works" steps, product-card outfit grid, and pill buttons in Samsung blue. Fully
  responsive. Uses the **Inter** font from Google Fonts (`index.html`), with a system-font
  fallback if offline.

---

## Tech stack

| Layer    | Tech                                                            |
| -------- | -------------------------------------------------------------- |
| Frontend | React 18 + Vite 6 (JavaScript)                                 |
| Backend  | Python + FastAPI + Uvicorn                                     |
| AI       | `gemini-2.5-flash` (analysis), `gemini-2.5-flash-image` (looks) |
| SDK      | `google-genai` (the Google Gen AI SDK)                         |

---

## How it works

1. **Upload** a full-body photo → `POST /api/analyze` returns the structured Style
   Blueprint (all 5 sections).
2. The report shows all 16–20 outfit suggestions as text. Every garment has a
   **🛒 Buy** link (Google Shopping search) for one-click purchasing.
3. Click **✨ Generate look** on any outfit → `POST /api/generate-outfit` renders the
   *same person* in that outfit, using their original photo for identity consistency.
   Images are generated on demand, one at a time.

---

## Architecture

```
Browser (React/Vite :5173)
   │  multipart photo
   ├──────────────► POST /api/analyze ──► gemini-2.5-flash (vision + response_schema)
   │  ◄── StyleBlueprint JSON
   │
   │  { image_b64, image_prompt }
   └──────────────► POST /api/generate-outfit ──► gemini-2.5-flash-image (restyle)
      ◄── { image_b64 } (PNG of the person in the outfit)

Buy links are built in the browser from each item's shopping_query
(https://www.google.com/search?tbm=shop&q=...) — no backend call, no extra cost.
```

In dev, the Vite server proxies `/api` → `http://localhost:8000`, so the browser sees a
single origin (no CORS friction).

---

## Project layout

```
iconik-ai/
├── README.md
├── .gitignore
├── backend/
│   ├── main.py            # FastAPI app, CORS, 2 endpoints, file validation
│   ├── gemini_service.py  # Gemini client + analyze_image() + generate_outfit_image()
│   ├── schemas.py         # Pydantic models = API shape AND Gemini response_schema
│   ├── prompts.py         # ANALYSIS_PROMPT + image-prompt builder
│   ├── requirements.txt   # pinned dependencies
│   └── .env.example       # GEMINI_API_KEY=
└── frontend/
    ├── package.json       # scripts invoke Vite via node (see "R&D path" note)
    ├── vite.config.js     # dev proxy /api -> :8000
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx            # upload → analyze → render report
        ├── api.js             # fetch wrappers (analyzePhoto, generateOutfit, fileToBase64)
        ├── shopping.js        # googleShoppingUrl(query) helper
        ├── styles.css
        └── components/
            ├── ImageUploader.jsx   # drag/drop + preview
            ├── BlueprintReport.jsx # renders the 5 sections
            ├── ColorPalette.jsx    # hex color swatches
            └── OutfitGallery.jsx   # outfit cards, Buy links, Generate-look
```

---

## Prerequisites

- **Python** 3.10+ (tested on 3.12)
- **Node.js** 18+ (tested on 24)
- A **Gemini API key** → https://aistudio.google.com/apikey

---

## Setup & run

### 1. Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env        # then edit .env and paste your GEMINI_API_KEY
uvicorn main:app --reload --port 8000
```

Interactive API docs (Swagger UI): http://localhost:8000/docs

### 2. Frontend (new terminal)

```powershell
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

Open http://localhost:5173.

> **Note — the `D:\Guvi\R&D` path contains an `&`.** On Windows, the `&` breaks npm's
> default `.bin` script shim. This project already works around it: `package.json`
> scripts invoke Vite via node directly (`node ./node_modules/vite/bin/vite.js`), so
> `npm run dev` / `npm run build` work normally. Also remember to **quote paths** in
> PowerShell when they include the `&`.

---

## Run with Docker

The whole app (frontend + backend) runs in **one container on port 9005** — FastAPI serves
both the API and the built React site, so there's only one port to expose.

**Prerequisite:** put your key in `backend/.env` (`GEMINI_API_KEY=...`). It's injected at
runtime via `env_file` and is **never baked into the image**.

```powershell
# from the iconik-ai/ folder
docker compose up --build        # add -d to run detached
```

Then open **http://localhost:9005** (API at `/api/...`, Swagger at `/docs`).

Stop it with `docker compose down`.

Single-container alternative (no compose):

```powershell
docker build -t vesti .
docker run -p 9005:9005 --env-file backend/.env vesti
```

How it works: a multi-stage `Dockerfile` builds the frontend (`node`) then copies the static
`dist/` into the Python image as `./static`; `main.py` mounts it so the SPA and `/api/*` are
served from the same origin (no CORS/proxy needed). Local dev is unaffected — without a
`./static` folder the backend stays API-only.

---

## API reference

Base URL (dev): `http://localhost:8000`

### `GET /api/health`
Liveness check. → `200 { "status": "ok" }`

### `POST /api/analyze`
Analyze a person photo and return the full Style Blueprint.

- **Request:** `multipart/form-data` with field **`photo`** (JPEG, PNG or WebP, ≤ 10 MB).
- **Response:** `200` — a `StyleBlueprint` JSON object (see structure below).
- **Errors:** `415` unsupported type · `413` too large · `400` empty file ·
  `500` missing API key · `502` Gemini/analysis failure. All return `{ "detail": "..." }`.

Example:
```powershell
curl.exe -F "photo=@person.jpg" http://localhost:8000/api/analyze
```

### `POST /api/generate-outfit`
Generate one image of the person wearing a specific outfit.

- **Request:** `application/json`
  ```json
  { "image_b64": "<base64 of the original photo, no data-URI prefix>",
    "image_prompt": "<the outfit's image_prompt from the blueprint>" }
  ```
- **Response:** `200` — `{ "image_b64": "<base64 PNG of the person in the outfit>" }`
- **Errors:** `400` invalid base64 · `500` missing API key · `502` generation failure
  (e.g. safety block).

---

## Style Blueprint data structure

`POST /api/analyze` returns:

```jsonc
{
  "overall_summary": "2–3 sentence personal style summary",
  "silhouette_profile": {
    "body_shape": "Rectangle | Hourglass | Triangle | …",
    "shoulder_hip_read": "…",
    "torso_length": "Short | Balanced | Long",
    "flattering_silhouettes": ["…"],
    "silhouettes_to_avoid": ["…"]
  },
  "facial_architecture": {
    "face_shape": "Oval | Round | Square | …",
    "recommended_necklines": ["…"],
    "earring_shapes": ["…"],
    "eyewear_shapes": ["…"]
  },
  "chromatic_harmony": {
    "skin_undertone": "Warm | Cool | Neutral",
    "season": "e.g. Warm Autumn",
    "flattering_colors": [{ "name": "Teal Blue", "hex": "#008080" }],  // ~10
    "avoid_colors":      [{ "name": "…", "hex": "#…" }]                // ~4
  },
  "outfit_formulas": [                                                  // 16–20
    {
      "occasion": "Smart Casual Office",
      "items": [
        { "category": "Top",       "description": "Cream silk blouse",
          "shopping_query": "cream silk blouse women" },               // → Buy link
        { "category": "Bottom",    "description": "Navy tailored trousers",
          "shopping_query": "navy tailored trousers women" },
        { "category": "Footwear",  "description": "Tan leather loafers",
          "shopping_query": "tan leather loafers" },
        { "category": "Accessory", "description": "Gold chain belt",
          "shopping_query": "gold chain belt" }
      ],
      "image_prompt": "A single vivid sentence describing the whole look"  // → Generate look
    }
  ],
  "concern_zone_solutions": [                                           // 3–6
    { "zone": "Midsection", "advice": "…" }
  ]
}
```

These models live in `backend/schemas.py` and double as the Gemini `response_schema`.

---

## Configuration

| What | Where | Default |
| ---- | ----- | ------- |
| Gemini API key | `backend/.env` → `GEMINI_API_KEY` | — (required) |
| Analysis model | `ANALYSIS_MODEL` in `backend/gemini_service.py` | `gemini-2.5-flash` |
| Image model | `IMAGE_MODEL` in `backend/gemini_service.py` | `gemini-2.5-flash-image` |
| Max upload size | `MAX_BYTES` in `backend/main.py` | 10 MB |
| Allowed types | `ALLOWED_TYPES` in `backend/main.py` | jpeg, png, webp |
| Allowed origins (CORS) | `CORSMiddleware` in `backend/main.py` | `localhost:5173` |
| Backend port | uvicorn `--port` | 8000 |
| Dev proxy target | `frontend/vite.config.js` | `http://localhost:8000` |
| Buy-link store | `frontend/src/shopping.js` | Google Shopping search |

For higher image quality, set `IMAGE_MODEL = "gemini-3.1-flash-image"`.

---

## Cost

- **Analysis** (`/api/analyze`) — one `gemini-2.5-flash` text+vision call per photo
  (low cost; priced per input/output token).
- **Image generation** (`/api/generate-outfit`) — `gemini-2.5-flash-image`, ~**$0.039
  per image**. Generated only when the user clicks **Generate look**, so a full
  blueprint with 20 outfits costs ~one analysis call unless the user renders looks.
- **Buy links** are plain Google Shopping search URLs — **free**, no API call.

---

## Troubleshooting

| Symptom | Fix |
| ------- | --- |
| `GEMINI_API_KEY is not set` (HTTP 500) | Create `backend/.env` from `.env.example` and paste your key; restart uvicorn. |
| `npm run dev` fails with a weird truncated path | The `&` in `D:\Guvi\R&D` — already handled via node-invoking scripts; make sure you're using this project's `package.json`. |
| PowerShell "ampersand (&) is not allowed" | Quote any path containing `&`, e.g. `cd "D:\Guvi\R&D\iconik-ai\backend"`. |
| 415 / 413 on upload | Use a JPEG/PNG/WebP ≤ 10 MB. |
| 502 on analyze/generate | Usually a Gemini quota limit or a safety block — try a clearer full-body photo or check your key's quota. |
| Buy link shows odd results | The `shopping_query` was vague; results improve with clearer source photos. You can tweak the query format in the prompt (`backend/prompts.py`). |

---

## Limitations & roadmap

Out of scope in this MVP (intentionally):
- Auth / user accounts / saved blueprints
- Payments & usage limits
- Persisting generated images (currently returned inline as base64, not stored)
- Affiliate monetization on Buy links (links are plain/convenience for now)

Possible next steps: "Shop the whole look" button, download blueprint as PDF, gallery of
saved looks, and switching to `gemini-3.1-flash-image` for higher-fidelity renders.

---

*For styling inspiration only. Powered by Google Gemini.*
