# 💎 Necklace Try-On

Upload a necklace image → generate a photorealistic image of a necklace worn by
an Indian model in a saree → edit the stones on that image (e.g. green → red),
keeping the rest of the photo unchanged.

Built for Assignment 2.

## Live app

- **App:** _<add your Streamlit Community Cloud URL here after deploy>_
- **Screen recording:** _<add link>_

## Backends

The app has two backends. It picks automatically:

| | When | Generate step | Edit / recolour step | Cost |
|---|---|---|---|---|
| **AI Horde** (default) | no key entered | text2img on SDXL — a realistic model in a saree wearing an ornate necklace; the necklace is **representative, not a pixel-match** of the upload | img2img recolour on the generated image — **faithful & repeatable** | free, no card, no daily cap (just a shared GPU queue — seconds to minutes) |
| **Bring your own key** | a Gemini `AIza…` or OpenAI `sk-…` key is entered | reference-faithful: the necklace is passed as an image | reference-faithful | your key's usage (~cents/image) |

**Why two:** no free image API allows unlimited faithful generation — every
top-tier model (`gpt-image-1`, Gemini image) is paid or hard-quota. So the live
app runs on AI Horde for free, unlimited access, and anyone who wants exact
fidelity (including for the demo recording) plugs in a key.

### Model selection — what was tried

- **OpenAI `gpt-image-1`** — no free tier (~$0.02–0.19/image).
- **Google Gemini image model ("Nano Banana")** — API returns `limit: 0`; image
  models have **no free API quota** (free only in the AI Studio website). A US
  host did not change this.
- **Hugging Face Inference API** (`Qwen-Image-Edit`, `FLUX.1-Kontext-dev`) — routes
  to paid partner providers → `401`.
- **Public HF Space + free token (Qwen-Image-Edit)** — real editing model, but the
  free ZeroGPU budget is ~4 min/day and would be drained by a single visitor.
- **Self-hosted Gradio Space (FLUX.2 [klein] on ZeroGPU)** — Hugging Face now
  requires PRO for any compute Space.
- **Pollinations.ai** — editing models behind a paid tier; keyless model ignores
  the reference.
- **Cloudflare Workers AI** — its only img2img model (SD 1.5) was withdrawn.
- **AI Horde** — genuinely free, no card, no hard daily cap. Chosen as the
  default, with an optional bring-your-own-key path for full fidelity.

## Tools / technologies

- **Python 3.13**, **Streamlit** — UI, state, hosting
- **requests** — AI Horde REST API
- **google-genai** / **openai** — the optional premium backends
- **Pillow** — image I/O and downscaling
- **Streamlit Community Cloud** — free deploy

## Prompting approach

Templates in [`prompts.py`](prompts.py):

- **Generation, reference path** (`GENERATION_PROMPT`) — the necklace is the input
  image. Framed as product photography, fixes the model (Indian woman, silk saree
  in a selectable colour, studio lighting, upper-chest crop, necklace as focal
  point), then a block of **fidelity constraints**: same shape / stone count /
  arrangement / colour / cut / pearls / metal tone, "do not redesign".
- **Generation, free path** (`GENERATION_PROMPT_NOREF`) — text2img, so the
  necklace is *described* (rose-gold, diamonds, emeralds, pearl drops) rather than
  copied; plus a strong negative prompt for anatomy artefacts.
- **Editing** (`EDIT_PROMPT`) — one localized instruction (default: green stones →
  red rubies of the same shape, size, position) with everything else pinned, so
  the model retouches rather than regenerates. Chained edits build on the last
  result; a low img2img `denoising_strength` keeps the necklace geometry.

## How design accuracy is preserved

- Reference path: the necklace photo is the model input, so it works from pixels.
- Free path: the recolour edit is img2img at low strength, so the generated
  necklace's shape is untouched and only the stone hue changes.
- The generation prompt enumerates the invariants instead of "keep it similar".

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

All keys optional — with none, it runs on AI Horde.

## Deploy (free)

1. Push to GitHub.
2. <https://share.streamlit.io> → **New app** → `app.py`.
3. **Settings → Secrets** — all optional:
   ```toml
   # Priority on the free queue (free key from stablehorde.net/register):
   HORDE_API_KEY = "..."
   # Premium backend for full fidelity (Gemini AIza… or OpenAI sk-…):
   BYOK_KEY = "..."
   ```

## Limitations faced

- **No free faithful generation.** Every model that can match the uploaded
  necklace is paid or hard-quota (see model-selection list). The free path's
  generate step is therefore representative, not exact.
- **AI Horde is a shared queue.** Under load, a run can take several minutes;
  anonymous access is lowest priority. A free Horde key helps a lot.
- **Free path is SDXL-tier.** Fine filigree and exact stone counts drift.
- **Edit localization.** Broad instructions can tint nearby areas; narrow ones
  work better.
- **Single upper-body view; non-deterministic between runs.**
