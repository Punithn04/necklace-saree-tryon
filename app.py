"""Necklace Try-On — Streamlit prototype.

Upload a necklace image -> generate a photorealistic image of the same necklace
worn by an Indian model in a saree -> edit the stones on that image (e.g. green
-> red). All generation runs on Gemini 2.5 Flash Image ("Nano Banana"), free tier.
"""

from __future__ import annotations

import io

import streamlit as st
from PIL import Image

from gemini_client import GeminiError, run
from prompts import DEFAULT_EDIT_INSTRUCTION, EDIT_PROMPT, GENERATION_PROMPT

st.set_page_config(page_title="Necklace Try-On", page_icon="💎", layout="wide")


def to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def load(upload) -> Image.Image:
    return Image.open(upload).convert("RGB")


def get_api_key() -> str | None:
    try:
        key = st.secrets.get("GEMINI_API_KEY", None)
    except Exception:
        key = None
    with st.sidebar:
        st.header("Setup")
        if key:
            st.success("Using GEMINI_API_KEY from app secrets.")
        else:
            key = st.text_input(
                "Gemini API key",
                type="password",
                help="Free key: https://aistudio.google.com/apikey",
            ) or None
        st.caption("Model: gemini-2.5-flash-image (Nano Banana), free tier.")
        st.caption(
            "The free image tier is blocked outside the US — run the deployed app "
            "on Streamlit Community Cloud (US) for it to work."
        )
    return key


def generate(api_key, prompt, images, label):
    with st.spinner(f"{label} with Gemini…"):
        try:
            return run(api_key, prompt, images)
        except GeminiError as e:
            st.error(str(e))
            return None


def main() -> None:
    st.title("💎 Necklace Try-On")
    st.write(
        "Upload a necklace image and generate a realistic photo of the same "
        "necklace worn by an Indian model in a saree — then tweak the stones."
    )

    api_key = get_api_key()
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
    if st.button("Generate", type="primary", disabled=not api_key):
        img = generate(
            api_key,
            GENERATION_PROMPT.format(saree_colour=saree_colour),
            [st.session_state.necklace_img],
            "Generating",
        )
        if img is not None:
            st.session_state.generated, st.session_state.edited = img, None
    if not api_key:
        st.warning("Add your Gemini API key in the sidebar to generate.")

    if st.session_state.generated is None:
        return
    st.image(st.session_state.generated, caption="Generated output", width=400)
    st.download_button("Download generated", to_png_bytes(st.session_state.generated),
                       file_name="necklace_on_model.png", mime="image/png")

    # ---- Step 3: edit ------------------------------------------------------
    st.subheader("3 · Edit the stones")
    instruction = st.text_area("Edit instruction", value=DEFAULT_EDIT_INSTRUCTION)
    if st.button("Apply edit", disabled=not api_key):
        base = st.session_state.edited or st.session_state.generated
        img = generate(api_key, EDIT_PROMPT.format(instruction=instruction), [base], "Editing")
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
