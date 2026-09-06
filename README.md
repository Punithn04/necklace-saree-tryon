---
title: Necklace Try-On
emoji: 💎
colorFrom: pink
colorTo: yellow
sdk: gradio
sdk_version: 5.9.1
app_file: app.py
pinned: false
short_description: Put a necklace on an Indian model in a saree, then recolour its stones
---

# 💎 Necklace Try-On

Upload a necklace image → generate a photorealistic image of the **same** necklace
worn by an Indian model in a saree → edit the stones on that image (e.g. green →
red), keeping the rest of the photo unchanged.

Built for Assignment 2. **The live app is this Hugging Face Space itself.**

## Model / API used

| | |
|---|---|
| Model | **FLUX.2 [klein]** (9B, Black Forest Labs) via `diffusers` |
| Hosting | **Hugging Face Space** (Gradio SDK) on **ZeroGPU** — free |
| Why | FLUX.2 takes one or more reference images plus a text instruction, so the same pipeline call both places the necklace on a model and does the targeted stone recolour, with strong reference fidelity. Running it on our own ZeroGPU Space keeps it free. |

`MODEL_ID` is a Space variable; the code falls back to
`black-forest-labs/FLUX.1-Kontext-dev` if a different FLUX.2 [klein] repo id is
needed.

### Model selection — what was tried first

- **OpenAI `gpt-image-1`** — no free tier.
- **Google Gemini image model ("Nano Banana")** — API returns `limit: 0`; no free
  API quota (free only in the AI Studio website).
- **Hugging Face Inference API** (`Qwen-Image-Edit`, `FLUX.1-Kontext-dev`) — routes
  to paid partner providers → `401`.
- **Calling other people's public Spaces** — ran into their per-caller ZeroGPU
  quota.
- **Pollinations.ai** — editing models behind a paid tier.
- **Cloudflare Workers AI** — the only img2img model (SD 1.5) was withdrawn.
- **AI Horde** — free img2img works for the *edit*, but plain SD img2img cannot
  synthesise a model wearing the necklace for the *generate* step.
- **Self-hosted ZeroGPU Space + FLUX.2 [klein]** — a real reference-editing model,
  on our own free GPU allowance. Chosen.

## How it works

`app.py` is a Gradio app with two GPU functions, both decorated `@spaces.GPU`:

1. **generate(necklace, saree_colour, …)** — builds the generation prompt for the
   chosen saree colour, passes the necklace as the reference image, returns the
   model shot.
2. **edit(image, instruction, …)** — passes the generated image back in with a
   localized instruction (default: green stones → red rubies), returns the edited
   image. Repeated edits chain off the previous result.

Both share `_infer()`, which fits the image to a multiple-of-16 size ≤ 1024 px
and calls the FLUX.2 pipeline with a fixed (or randomised) seed.

## Prompting approach

Two templates in [`prompts.py`](prompts.py):

1. **Generation** — the necklace is the reference image, not described in text.
   The prompt frames the task as product photography, fixes the model (Indian
   woman, silk saree in a selectable colour, studio lighting, upper-chest crop
   with the necklace as focal point), then spends most of its length on
   **fidelity constraints**: same shape, same stone count / arrangement / colour /
   cut, same pearl drops, same metal tone — "match it like a photograph, not an
   interpretation", plus "do not redesign / add / remove / recolour".
2. **Editing** — one localized instruction with everything else pinned (face,
   pose, saree, background, lighting, metalwork, pearls, other stones) so the
   model retouches rather than regenerates.

## How design accuracy is preserved

- The necklace photo is always the reference image, so the model works from
  pixels, not a paraphrase.
- The generation prompt enumerates the invariants instead of "keep it similar".
- Editing is scoped to one attribute and forbids touching the rest; chained edits
  build on the last result; a fixed seed keeps runs reproducible.

## Deploy this Space (free)

1. Create a new **Space** at <https://huggingface.co/new-space> → SDK **Gradio**.
2. In **Settings → Hardware**, select **ZeroGPU**.
3. Push these files to the Space's git repo (or "Files → add" in the UI).
4. If FLUX.2 [klein] is gated, accept its licence on its model page, then add a
   Space secret **`HF_TOKEN`** (a Read token). Optionally set **`MODEL_ID`**.
5. First build downloads the weights (a few minutes); after that it runs on
   ZeroGPU per request.

Source mirror: <https://github.com/Punithn04/necklace-saree-tryon>

## Run locally (needs a CUDA GPU with enough VRAM)

```bash
pip install -r requirements.txt
python app.py
```

## Limitations faced

- **Free-tier reality** — no ChatGPT-quality image *API* is free; every hosted
  free API was a dead end (see above), so the model is self-hosted on ZeroGPU.
- **ZeroGPU daily budget** — the free allowance is limited; heavy use hits a
  "quota exceeded, try later" message. A `klein`-sized model at fewer steps
  stretches it further than a larger model would.
- **Cold starts** — the first request after the Space sleeps reloads the pipeline
  (tens of seconds).
- **Stone-level fidelity** — silhouette and palette hold up well; very fine
  filigree and exact counts of tiny accent stones can still drift.
- **Single upper-body view; non-deterministic unless the seed is fixed.**
