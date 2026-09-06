"""Necklace Try-On — Gradio app for a Hugging Face ZeroGPU Space.

Upload a necklace image -> generate the same necklace worn by an Indian model in
a saree -> recolour the stones (e.g. green -> red).

Backbone: FLUX.2 [klein] (9B) loaded with diffusers, run on ZeroGPU. FLUX.2
takes one or more reference images plus a text instruction, so the same pipeline
call does both the generation and the edit.
"""

from __future__ import annotations

import os
import random

import gradio as gr
import spaces
import torch
from PIL import Image

from prompts import DEFAULT_EDIT_INSTRUCTION, EDIT_PROMPT, GENERATION_PROMPT

# FLUX.2 [klein]. Override with a Space variable if the final repo id differs.
# Safe fallback that is known-good for reference editing: black-forest-labs/FLUX.1-Kontext-dev
MODEL_ID = os.environ.get("MODEL_ID", "black-forest-labs/FLUX.2-klein-dev")
DTYPE = torch.bfloat16
MAX_SIDE = 1024
MAX_SEED = 2**31 - 1

_pipe = None


def _load():
    global _pipe
    if _pipe is not None:
        return _pipe
    from diffusers import DiffusionPipeline

    _pipe = DiffusionPipeline.from_pretrained(
        MODEL_ID,
        torch_dtype=DTYPE,
        token=os.environ.get("HF_TOKEN"),
    )
    _pipe.to("cuda")
    try:
        _pipe.enable_attention_slicing()
    except Exception:
        pass
    return _pipe


def _fit(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > MAX_SIDE:
        s = MAX_SIDE / max(w, h)
        w, h = round(w * s), round(h * s)
    w, h = w - w % 16, h - h % 16
    return img.resize((max(w, 512), max(h, 512)), Image.LANCZOS)


def _infer(refs: list[Image.Image], prompt: str, steps: int, guidance: float, seed: int) -> Image.Image:
    pipe = _load()
    gen = torch.Generator(device="cuda").manual_seed(int(seed))
    refs = [_fit(r) for r in refs]
    # FLUX.2 accepts reference images via `image=` (list). If a given build uses a
    # different kwarg, adjust here.
    out = pipe(
        prompt=prompt,
        image=refs if len(refs) > 1 else refs[0],
        num_inference_steps=int(steps),
        guidance_scale=float(guidance),
        generator=gen,
    )
    return out.images[0]


@spaces.GPU(duration=150)
def generate(necklace, saree_colour, steps, guidance, seed, randomize):
    if necklace is None:
        raise gr.Error("Upload a necklace image first.")
    if randomize:
        seed = random.randint(0, MAX_SEED)
    prompt = GENERATION_PROMPT.format(saree_colour=saree_colour)
    img = _infer([necklace], prompt, steps, guidance, seed)
    return img, seed


@spaces.GPU(duration=150)
def edit(base_image, instruction, steps, guidance, seed, randomize):
    if base_image is None:
        raise gr.Error("Generate an image first (or upload one to the Generated box).")
    if randomize:
        seed = random.randint(0, MAX_SEED)
    prompt = EDIT_PROMPT.format(instruction=instruction or DEFAULT_EDIT_INSTRUCTION)
    img = _infer([base_image], prompt, steps, guidance, seed)
    return img, seed


SAREE_COLOURS = ["cream and gold", "deep red", "royal blue", "emerald green", "magenta pink"]

with gr.Blocks(title="Necklace Try-On", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        "# 💎 Necklace Try-On\n"
        "Upload a necklace → generate it worn by an Indian model in a saree → "
        "recolour the stones. Runs FLUX.2 [klein] on ZeroGPU."
    )

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 1 · Upload a necklace")
            necklace = gr.Image(label="Necklace", type="pil", height=320)
            saree = gr.Dropdown(SAREE_COLOURS, value=SAREE_COLOURS[0], label="Saree colour")
            gen_btn = gr.Button("Generate", variant="primary")

        with gr.Column():
            gr.Markdown("### 2 · Generated")
            generated = gr.Image(label="Model shot", type="pil", height=360)
            gr.Markdown("### 3 · Edit the stones")
            instruction = gr.Textbox(
                value=DEFAULT_EDIT_INSTRUCTION, label="Edit instruction", lines=2
            )
            edit_btn = gr.Button("Apply edit")
            edited = gr.Image(label="Edited", type="pil", height=360)

    with gr.Accordion("Advanced", open=False):
        steps = gr.Slider(4, 50, value=28, step=1, label="Inference steps")
        guidance = gr.Slider(1.0, 8.0, value=3.5, step=0.1, label="Guidance scale")
        seed = gr.Number(value=42, precision=0, label="Seed")
        randomize = gr.Checkbox(value=False, label="Randomize seed each run")

    if os.path.exists("sample_images/necklace_green.jpg"):
        gr.Examples(
            examples=[["sample_images/necklace_green.jpg"], ["sample_images/necklace_red.jpg"]],
            inputs=[necklace],
            label="Samples",
        )

    gen_btn.click(
        generate,
        [necklace, saree, steps, guidance, seed, randomize],
        [generated, seed],
    )
    edit_btn.click(
        edit,
        [generated, instruction, steps, guidance, seed, randomize],
        [edited, seed],
    )

if __name__ == "__main__":
    demo.queue(max_size=12).launch()
