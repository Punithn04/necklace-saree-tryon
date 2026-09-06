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
| Model | **Stable Diffusion 1.5** (img2img) — the only image-input model on Workers AI |
| API | **Cloudflare Workers AI** — `@cf/runwayml/stable-diffusion-v1-5-img2img` |
| Free tier | **10,000 Neurons/day**, no card — just a free Cloudflare account |
| Auth | Account ID + a "Workers AI" API token |

Both steps use the same img2img call. A `strength` parameter controls how far the
model may move from the input image:

- **generate** — `strength ≈ 0.85` (large change: put the necklace on a model)
- **edit** — `strength ≈ 0.45` (small change: recolour the stones, keep the rest)

### Model selection — what was tried

- **OpenAI `gpt-image-1`** — no free tier (~$0.02–0.19/image).
- **Google Gemini image model ("Nano Banana")** — API returns `limit: 0`; image
  models have **no free API quota** (free only in the AI Studio website).
- **Hugging Face Inference API** (`Qwen-Image-Edit`, `FLUX.1-Kontext-dev`) — routes
  to paid partner providers → `401`.
- **Hugging Face Space + free token (Qwen-Image-Edit)** — real editing model, but
  the free ZeroGPU budget is only a few minutes/day and was exhausted quickly.
- **Pollinations.ai** — editing models behind a paid tier; keyless model ignores
  the reference.
- **Cloudflare Workers AI (SD 1.5 img2img)** — a genuine free tier with a large
  daily allowance. Chosen, accepting lower fidelity than the paid models.

## Tools / technologies

- **Python 3.13**, **Streamlit** — UI, state, hosting
- **requests** — Cloudflare Workers AI REST calls
- **Pillow** — image I/O, downscaling (768 px longest side), PNG export
- **Streamlit Community Cloud** — free deploy

## Prompting approach

Two templates in [`prompts.py`](prompts.py):

1. **Generation** — the necklace image is the img2img input, not described in
   text. The prompt frames the task as product photography, fixes the model
   (Indian woman, silk saree in a selectable colour, studio lighting, upper-chest
   crop with the necklace as focal point), then spends most of its length on
   **fidelity constraints**: same shape, same stone count / arrangement / colour /
   cut, same pearl drops, same metal tone — "match it like a photograph, not an
   interpretation", plus "do not redesign / add / remove / recolour".
2. **Editing** — one localized instruction (default: green stones → red rubies of
   the same shape, size and position), with a low `strength` so most of the
   generated photo is preserved. A strong negative prompt suppresses text,
   watermarks and anatomy artefacts. Repeated edits chain off the previous
   result.

## How design accuracy is preserved

- The necklace photo is always the img2img input, so the model starts from the
  real pixels rather than a paraphrase.
- Per-step `strength`: high for placing the necklace, low for the recolour so the
  necklace geometry barely moves.
- The generation prompt enumerates the invariants instead of "keep it similar".
- Chained edits build on the last result.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Enter your Cloudflare Account ID + API token in the sidebar, or set `CF_ACCOUNT_ID`
and `CF_API_TOKEN` in `.streamlit/secrets.toml`.

## Deploy (free)

1. Push this repo to GitHub.
2. <https://share.streamlit.io> → **New app** → point at `app.py`.
3. **Settings → Secrets:**
   ```toml
   CF_ACCOUNT_ID = "..."
   CF_API_TOKEN = "..."
   ```

## Limitations faced

- **No free-tier API from the ChatGPT-quality models** — Gemini's image API is
  `limit: 0`, OpenAI's is paid, HF's free GPU budget is minutes/day. The only
  large free allowance is Cloudflare's, on SD 1.5.
- **SD 1.5 img2img fidelity is limited.** It keeps the necklace's rough shape and
  palette, but fine filigree, exact stone counts and small accent stones drift
  more than a dedicated edit model would.
- **`strength` is a blunt instrument** — too low and the "generate" step barely
  adds a model; too high and the "edit" step changes more than the stones. The
  values are tuned but not perfect.
- **No true masking**, so a broad recolour instruction can tint nearby areas.
- **Single upper-body view; non-deterministic between runs.**
