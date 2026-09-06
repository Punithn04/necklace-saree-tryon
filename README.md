# 💎 Necklace Try-On

A hosted prototype that takes a necklace image, builds an optimised prompt to
place it on an Indian model in a saree, and to recolour its stones (e.g. green →
red) — then collects the results into an input → generated → edited comparison
with downloads.

Built for Assignment 2.

## Live app

- **App:** _<add your Streamlit Community Cloud URL here after deploy>_
- **Screen recording:** _<add link>_

## How it works

The app does everything except the single model call, so it stays **completely
free — no API keys, no quotas, no cost**:

1. **Upload** a necklace image (or use a bundled sample). Download it to attach in
   the image tool.
2. **Generate** — pick a saree colour; the app builds a detailed generation
   prompt. Run it in **ChatGPT** or **Google AI Studio** (both free in the
   browser) with the necklace attached, then upload the result back.
3. **Edit** — the app builds a localized edit prompt (default: green stones → red
   rubies). Run it in the *same* chat so it edits the image it just made, then
   upload the edited image back.
4. **Result** — input → generated → edited strip, with download buttons.

Recommended model in the web tool: **Gemini 2.5 Flash Image ("Nano Banana")** or
**GPT-4o image** — both reproduce the necklace faithfully from the attached
reference.

## Why this design — free-tier model selection

The assignment requires a free-tier model. Every free *API* for
reference-faithful image editing was tested and rejected:

| Option | Outcome |
|---|---|
| **Google Gemini image API** ("Nano Banana") | `limit: 0` — no free API quota (free only in the AI Studio website); Indian billing requires a paid prepaid top-up |
| **OpenAI `gpt-image-1`** | No free tier (~₹1–14 / image) |
| **Hugging Face Inference API** (Qwen-Image-Edit, FLUX.1-Kontext-dev) | Routes to paid partner providers → `401` |
| **Hugging Face Spaces / ZeroGPU** | ~4 min GPU/day — one visitor drains it; self-hosting a Space now needs a paid HF plan |
| **Cloudflare Workers AI** | All image-to-image models withdrawn |
| **Pollinations.ai** | Editing models behind a paid tier; the free one ignores the reference image |
| **AI Horde** (free, unlimited) | Recolour edit works faithfully, but plain Stable Diffusion cannot place the *exact* uploaded necklace on a generated model |

Conclusion: a fully free **and** fully automatic **and** design-accurate version
is not currently possible — every model that reproduces the necklace faithfully
is paid or hard-quota-limited. So the app automates everything else and hands the
single generation/edit call to a free browser tool.

A small paid variant (OpenAI image API, ~₹4/image, with per-session rate limiting)
is available on request; it changes only the one model call.

## Prompting approach

Two templates in [`prompts.py`](prompts.py):

1. **Generation** — the necklace is attached as a reference image, not described.
   The prompt frames the task as product photography, fixes the model (Indian
   woman, silk saree in a selectable colour, studio lighting, upper-chest crop
   with the necklace as focal point), then spends most of its length on
   **fidelity constraints**: same shape, stone count, arrangement, colours, cuts,
   pearl drops, metal tone — "match it like a photograph, not an interpretation",
   plus "do not redesign / add / remove / recolour".
2. **Editing** — one localized instruction with everything else pinned (face,
   pose, saree, background, lighting, metalwork, pearls, other stones) so the
   model retouches rather than regenerates. Run in the same chat for consistency.

## How design accuracy is preserved

- The necklace photo is always attached, so the model works from pixels, not a
  paraphrase.
- The generation prompt enumerates the invariants instead of "keep it similar".
- The edit is scoped to one attribute and forbids touching the rest; it chains
  off the generated image in the same conversation.

## Tools / technologies

- **Python 3.13**, **Streamlit** — UI, state, hosting
- **Pillow** — image I/O and PNG export
- **Streamlit Community Cloud** — free deploy
- **ChatGPT (GPT-4o)** / **Google AI Studio (Gemini 2.5 Flash Image)** — the model call

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (free)

1. Push to GitHub.
2. <https://share.streamlit.io> → **New app** → point at `app.py`. No secrets.

## Limitations faced

- **No usable free image API** for reference-faithful generation/editing — hence
  the single manual model call (see the table above).
- **Manual step** — the user copies a prompt and uploads a result twice.
- **Model-dependent fidelity** — GPT-4o / Nano Banana hold the necklace well;
  fine filigree and exact counts of tiny accent stones can still drift.
- **Edit localization** — broad instructions can nudge lighting or a pearl; narrow
  instructions work better.
- **Single upper-body view; non-deterministic between runs.**
