"""Necklace Try-On — Streamlit prototype.

Upload a necklace image -> generate a photo of the same necklace worn by an
Indian model in a saree -> edit the stones on that image (e.g. green -> red).
All image work runs on the free AI Horde (stablehorde.net), img2img.
"""

from __future__ import annotations

import io

import streamlit as st
from PIL import Image

from horde_client import HordeError, run
from prompts import DEFAULT_EDIT_INSTRUCTION, EDIT_PROMPT, GENERATION_PROMPT

st.set_page_config(page_title="Necklace Try-On", page_icon="💎", layout="wide")


def to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def load(upload) -> Image.Image:
    return Image.open(upload).convert("RGB")


def get_key() -> str:
    try:
        key = st.secrets.get("HORDE_API_KEY", None)
    except Exception:
        key = None
    with st.sidebar:
        st.header("Setup")
        if key:
            st.success("Using HORDE_API_KEY from app secrets.")
        else:
            key = st.text_input(
                "AI Horde API key (optional)",
                type="password",
                help="Free key: https://stablehorde.net/register . Blank = anonymous (slower).",
            )
        st.caption("Model: SDXL img2img on the free AI Horde (stablehorde.net).")
        st.caption(
            "It's a shared volunteer GPU queue — a run can take 1–10 min. "
            "Anonymous is slowest; a free key jumps the queue."
        )
    return key or ""


def generate(key, step, prompt, images, label):
    box = st.empty()
    box.info(f"{label} on AI Horde — submitting…")

    def prog(msg):
        box.info(f"{label} on AI Horde — {msg}")

    try:
        img = run(key, step, prompt, images, progress=prog)
        box.empty()
        return img
    except HordeError as e:
        box.empty()
        st.error(str(e))
        return None


def main() -> None:
    st.title("💎 Necklace Try-On")
    st.write(
        "Upload a necklace image and generate a realistic photo of the same "
        "necklace worn by an Indian model in a saree — then tweak the stones."
    )

    key = get_key()
    for k in ("necklace_img", "generated", "edited"):
        st.session_state.setdefault(k, None)

    # ---- Step 1: upload ---------------------------------------------------------
    st.subheader("1 · Upload a necklace")
    up = st.file_uploader("Necklace image (JPG / PNG)", type=["jpg", "jpeg", "png"])
    c = st.columns(3)
    if c[0].button("Use sample: green stones"):
        st.session_state.necklace_img = Image.open("sample_images/necklace_green.jpg").convert("RGB")
        st.session_state.generated = st.session_state.edited = None
    if c[1].button("Use sample: red stones"):
        st.session_state.necklace_img = Image.open("sample_images/necklace_red.jpg").convert("RGB")
        st.session_state.generated = st.session_state.edited = None
    if up is not None:
        st.session_state.necklace_img = load(up)
        st.session_state.generated = st.session_state.edited = None

    if st.session_state.necklace_img is None:
        st.info("Upload a necklace image or pick a sample to begin.")
        return
    st.image(st.session_state.necklace_img, caption="Input necklace", width=300)

    # ---- Step 2: generate ----------------------------------------------------
    st.subheader("2 · Generate the model shot")
    saree_colour = st.selectbox(
        "Saree colour",
        ["cream and gold", "deep red", "royal blue", "emerald green", "magenta pink"],
    )
    if st.button("Generate", type="primary"):
        img = generate(
            key, "generate",
            GENERATION_PROMPT.format(saree_colour=saree_colour),
            [st.session_state.necklace_img],
            "Generating",
        )
        if img is not None:
            st.session_state.generated, st.session_state.edited = img, None

    if st.session_state.generated is None:
        return
    st.image(st.session_state.generated, caption="Generated output", width=400)
    st.download_button("Download generated", to_png_bytes(st.session_state.generated),
                       file_name="necklace_on_model.png", mime="image/png")

    # ---- Step 3: edit ------------------------------------------------------
    st.subheader("3 · Edit the stones")
    instruction = st.text_area("Edit instruction", value=DEFAULT_EDIT_INSTRUCTION)
    if st.button("Apply edit"):
        base = st.session_state.edited or st.session_state.generated
        img = generate(key, "edit", EDIT_PROMPT.format(instruction=instruction), [base], "Editing")
        if img is not None:
            st.session_state.edited = img

    if st.session_state.edited is not None:
        c1, c2 = st.columns(2)
        c1.image(st.session_state.generated, caption="Before", use_container_width=True)
        c2.image(st.session_state.edited, caption="Edited output", use_container_width=True)
        st.download_button("Download edited", to_png_bytes(st.session_state.edited),
                           file_name="necklace_edited.png", mime="image/png")


if __name__ == "__main__":
    main()
