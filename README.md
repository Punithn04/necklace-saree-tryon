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
| Model | **Qwen-Image-Edit** (Alibaba) — instruction-based image editing |
| API | Public **Hugging Face Space**, called via `gradio_client`; **free tier** |
| Auth | A free Hugging Face token ("Read" scope) — no card |
| Why | It takes an image + a text instruction and returns an image, so one call both places the necklace on a model and does the targeted stone recolour. It is a genuine free-tier path (no paid API). |

The Space runs on **ZeroGPU**: a free token grants a few minutes of GPU per day —
enough to build the deliverables and record the demo. Each run takes ~30–90s.

### Model selection — what was tried

- **OpenAI `gpt-image-1`** — no free tier (~$0.02–0.19/image).
- **Google Gemini image model ("Nano Banana")** — the API returns
  `RESOURCE_EXHAUSTED` / `limit: 0`; the image models have **no free API quota**
  (free only in the AI Studio website). Deploying in the US did not change this.
- **Hugging Face Inference API** (`Qwen-Image-Edit`, `FLUX.1-Kontext-dev`) — routed
  to paid partner providers → `401`.
- **Pollinations.ai** — editing models moved behind a paid tier; the keyless
  model ignored the reference necklace.
- **Hugging Face Space + free token (Qwen-Image-Edit)** — a real free-tier editing
  model. Chosen, accepting the small daily GPU budget.

## Tools / technologies

- **Python 3.13**, **Streamlit** — UI, state, hosting
- **gradio_client** — calls the Hugging Face Space
- **Pillow** — image I/O and downscaling (1024 px longest side)
- **Streamlit Community Cloud** — free deploy

## Prompting approach

Two templates in [`prompts.py`](prompts.py):

1. **Generation** — the necklace is passed as the input image, not described in
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
   edited image. `rewrite_prompt` is disabled on the Space so our prompt is used
   verbatim; a fixed seed keeps runs reproducible.

## How design accuracy is preserved

- The necklace photo is always an input image, so the model copies from pixels.
- The generation prompt enumerates the invariants (stone count, arrangement,
  cuts, pearls, metal tone) instead of a generic "keep it similar".
- Editing is scoped to one attribute and forbids touching the rest; chained edits
  build on the last result.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Paste a free HF token in the sidebar, or set `HF_TOKEN` in
`.streamlit/secrets.toml`.

## Deploy (free)

1. Push this repo to GitHub.
2. <https://share.streamlit.io> → **New app** → point at `app.py`.
3. **Settings → Secrets:**
   ```toml
   HF_TOKEN = "hf_..."
   ```

## Limitations faced

- **No free-tier API from the ChatGPT-quality models** — Gemini's image API is
  `limit: 0`, OpenAI's is paid. This is why the app uses Qwen-Image-Edit.
- **Daily GPU budget.** The free HF ZeroGPU allowance is a few minutes/day; heavy
  use hits a "quota exceeded, try again tomorrow" error (surfaced in the UI).
- **Latency.** Cold Space + queue means 30–90s per run.
- **Stone-level fidelity is imperfect.** The necklace silhouette and palette hold
  up, but fine filigree and the exact count of small accent stones can drift.
- **Edit localization.** Broad instructions can nudge lighting or a pearl; narrow
  instructions work better.
- **Single upper-body view; non-deterministic across prompts.**
