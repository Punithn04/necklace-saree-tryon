# 💎 Necklace Try-On

Upload a necklace image → generate a photorealistic image of the **same** necklace
worn by an Indian model in a saree → edit the stones on that image (e.g. green →
red), keeping the rest of the photo unchanged.

Built for Assignment 2.

## Live app

- **App:** _<add your Streamlit Community Cloud URL here after deploy>_
- **Screen recording:** _<add link>_

## Model / API used

| | |
|---|---|
| Model | **`gemini-2.5-flash-image`** — Google's "Nano Banana" image model |
| API | Google Gemini API, **free tier** (AI Studio key, no card) |
| Why | Native image-in / image-out: one call both places the necklace on a model and does the targeted stone recolour. Same quality tier as ChatGPT's image generation, but with a free API. |

### Free-tier / region note

The Gemini image model returns `RESOURCE_EXHAUSTED` with `limit: 0` when the
request comes from certain regions (India, EU, UK). The key is **not** the
problem — the request **origin IP** is. Running the deployed app on **Streamlit
Community Cloud** (US servers) uses the free quota normally. For local testing
from a blocked region, use a US VPN.

### Model selection — what was tried and rejected

- **OpenAI `gpt-image-1`** — no free tier (~$0.02–0.19/image).
- **Hugging Face Inference API** (`Qwen-Image-Edit`, `FLUX.1-Kontext-dev`) — route
  to paid partner providers → `401`.
- **Hugging Face Spaces** (ZeroGPU) — anonymous GPU quota is seconds/day.
- **Pollinations.ai** — editing models moved behind a paid tier; the keyless
  model ignored the reference necklace.
- **Gemini 2.5 Flash Image** — free API, top-tier quality, and the `limit: 0`
  is fixable by hosting in the US. Chosen.

## Tools / technologies

- **Python 3.13**, **Streamlit** — UI, state, hosting
- **google-genai** — Gemini API client
- **Pillow** — image I/O and downscaling
- **Streamlit Community Cloud** — free deploy (and the US egress that makes the
  free Gemini tier usable)

## Prompting approach

Two templates in [`prompts.py`](prompts.py):

1. **Generation** — the necklace is passed as an input image, not described in
   text. The prompt frames the task as product photography, fixes the model
   (Indian woman, silk saree in a selectable colour, studio lighting, upper-chest
   crop with the necklace as focal point), then spends most of its length on
   **fidelity constraints**: same shape, same stone count / arrangement / colour /
   cut, same pearl drops, same metal tone — "match it like a photograph, not an
   interpretation", plus an explicit "do not redesign / add / remove / recolour".
2. **Editing** — one localized instruction (default: green stones → red rubies of
   the same shape, size and position). Everything else is pinned — face, pose,
   saree, background, lighting, metalwork, pearls, other stones — so the model
   retouches rather than regenerates. Repeated edits chain off the previous
   edited image for consistency.

## How design accuracy is preserved

- The necklace photo is always an input image, so the model copies from pixels
  rather than a paraphrase.
- The generation prompt enumerates the invariants (stone count, arrangement,
  cuts, pearls, metal tone) instead of a generic "keep it similar".
- Editing is scoped to one attribute and explicitly forbids touching the rest;
  chained edits build on the last result.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Paste a free Gemini key in the sidebar (or set `GEMINI_API_KEY` in
`.streamlit/secrets.toml`). From a blocked region, run behind a US VPN.

## Deploy (free)

1. Push this repo to GitHub.
2. <https://share.streamlit.io> → **New app** → point at `app.py`.
3. **Settings → Secrets:**
   ```toml
   GEMINI_API_KEY = "..."
   ```

Deploying on Streamlit Cloud (US) is what makes the free Gemini image tier work.

## Limitations faced

- **Free image tier is geo-blocked** outside the US; the app must be hosted in
  the US (or run behind a US VPN locally).
- **Stone-level fidelity is imperfect.** The necklace silhouette and palette hold
  up well, but fine filigree and the exact count of small accent stones can drift.
- **Edit localization.** Broad instructions ("change the stones") can occasionally
  nudge lighting or an adjacent pearl; narrow instructions work better.
- **Non-determinism.** Same input, different runs → different photos; no seed
  control is exposed.
- **Single view.** Output is one upper-body crop; no multi-angle or full-length
  shots.
