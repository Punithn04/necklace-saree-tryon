"""Necklace Try-On — Streamlit prototype.

Upload a necklace image -> generate a photo of the same necklace worn by an
Indian model in a saree -> edit the stones on that image (e.g. green -> red).
All image work runs on Qwen-Image-Edit via a free Hugging Face Space.
"""

from __future__ import annotations

import io

import streamlit as st
from PIL import Image

from hf_client import HFError, run
from prompts import DEFAULT_EDIT_INSTRUCTION, EDIT_PROMPT, GENERATION_PROMPT

st.set_page_config(page_title="Necklace Try-On", page_icon="💎", layout="wide")


def to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def load(upload) -> Image.Image:
    return Image.open(upload).convert("RGB")


def get_token() -> str | None:
    try:
        tok = st.secrets.get("HF_TOKEN", None)
    except Exception:
        tok = None
    with st.sidebar:
        st.header("Setup")
        if tok:
            st.success("Using HF_TOKEN from app secrets.")
        else:
            tok = st.text_input(
                "Hugging Face token",
                type="password",
                help="Free, 'Read' scope: https://huggingface.co/settings/tokens",
            ) or None
        st.caption("Model: Qwen-Image-Edit (Hugging Face Space, free tier).")
        st.caption(
            "Runs on ZeroGPU — a free token gives a few minutes of GPU per day, "
            "and each run can take 30–90s."
        )
    return tok


def generate(token, prompt, images, label):
    with st.spinner(f"{label} on Hugging Face… (30–90s)"):
        try:
            return run(token, prompt, images)
        except HFError as e:
            st.error(str(e))
            return None


def main() -> None:
    st.title("💎 Necklace Try-On")
    st.write(
        "Upload a necklace image and generate a realistic photo of the same "
        "necklace worn by an Indian model in a saree — then tweak the stones."
    )

    token = get_token()
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
    if st.button("Generate", type="primary", disabled=not token):
        img = generate(
            token,
            GENERATION_PROMPT.format(saree_colour=saree_colour),
            [st.session_state.necklace_img],
            "Generating",
        )
        if img is not None:
            st.session_state.generated, st.session_state.edited = img, None
    if not token:
        st.warning("Add your Hugging Face token in the sidebar to generate.")

    if st.session_state.generated is None:
        return
    st.image(st.session_state.generated, caption="Generated output", width=400)
    st.download_button("Download generated", to_png_bytes(st.session_state.generated),
                       file_name="necklace_on_model.png", mime="image/png")

    # ---- Step 3: edit ------------------------------------------------------
    st.subheader("3 · Edit the stones")
    instruction = st.text_area("Edit instruction", value=DEFAULT_EDIT_INSTRUCTION)
    if st.button("Apply edit", disabled=not token):
        base = st.session_state.edited or st.session_state.generated
        img = generate(token, EDIT_PROMPT.format(instruction=instruction), [base], "Editing")
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
