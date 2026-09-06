"""Necklace Try-On — Streamlit prototype.

Upload a necklace image -> generate a photo of the same necklace worn by an
Indian model in a saree -> edit the stones (e.g. green -> red).

Backend:
  * default — AI Horde (stablehorde.net): free, no card, no daily cap (just a
    queue). The recolour edit is faithful; the generate step is text2img, so the
    necklace is a plausible one, not a pixel-match of the upload.
  * optional — paste a Gemini (AIza…) or OpenAI (sk-…) key for a reference-faithful
    result at your own cost.
"""

from __future__ import annotations

import io

import streamlit as st
from PIL import Image

from byok_client import BYOKError, run as byok_run
from horde_client import HordeError, run as horde_run
from prompts import (
    DEFAULT_EDIT_INSTRUCTION,
    EDIT_PROMPT,
    GENERATION_PROMPT,
    GENERATION_PROMPT_NOREF,
)

st.set_page_config(page_title="Necklace Try-On", page_icon="💎", layout="wide")


def to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def load(upload) -> Image.Image:
    return Image.open(upload).convert("RGB")


def _secret(name):
    try:
        return st.secrets.get(name, None)
    except Exception:
        return None


def sidebar() -> tuple[str | None, str]:
    with st.sidebar:
        st.header("Setup")
        byok = _secret("BYOK_KEY")
        horde_key = _secret("HORDE_API_KEY") or ""
        if byok:
            st.success("Using BYOK_KEY from app secrets (premium backend).")
        else:
            byok = st.text_input(
                "API key — optional, for best quality",
                type="password",
                help="Gemini key (AIza…) or OpenAI key (sk-…). Leave blank to use the free backend.",
            ) or None
        if not _secret("HORDE_API_KEY"):
            horde_key = st.text_input(
                "AI Horde key — optional (speeds the queue)",
                type="password",
                value="",
                help="Free from https://stablehorde.net/register . Blank = anonymous.",
            ) or ""

        if byok:
            st.info("Backend: **premium (your key)** — reference-faithful.")
        else:
            st.info(
                "Backend: **AI Horde (free)** — recolour is faithful; the generate "
                "step is text2img, so the necklace is representative, not exact."
            )
    return byok, horde_key


def do_generate(byok, horde_key, saree_colour, necklace):
    if byok:
        with st.spinner("Generating with your key…"):
            try:
                return byok_run(byok, GENERATION_PROMPT.format(saree_colour=saree_colour), [necklace])
            except BYOKError as e:
                st.error(str(e))
                return None
    box = st.empty()
    box.info("Generating on AI Horde — submitting…")
    try:
        return horde_run(
            horde_key, "generate",
            GENERATION_PROMPT_NOREF.format(saree_colour=saree_colour),
            [necklace],
            progress=lambda m: box.info(f"Generating on AI Horde — {m}"),
        )
    except HordeError as e:
        st.error(str(e))
        return None
    finally:
        box.empty()


def do_edit(byok, horde_key, instruction, base):
    prompt = EDIT_PROMPT.format(instruction=instruction or DEFAULT_EDIT_INSTRUCTION)
    if byok:
        with st.spinner("Editing with your key…"):
            try:
                return byok_run(byok, prompt, [base])
            except BYOKError as e:
                st.error(str(e))
                return None
    box = st.empty()
    box.info("Editing on AI Horde — submitting…")
    try:
        return horde_run(horde_key, "edit", prompt, [base],
                         progress=lambda m: box.info(f"Editing on AI Horde — {m}"))
    except HordeError as e:
        st.error(str(e))
        return None
    finally:
        box.empty()


def main() -> None:
    st.title("💎 Necklace Try-On")
    st.write(
        "Upload a necklace image and generate a realistic photo of the same "
        "necklace worn by an Indian model in a saree — then tweak the stones."
    )

    byok, horde_key = sidebar()
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
        img = do_generate(byok, horde_key, saree_colour, st.session_state.necklace_img)
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
        img = do_edit(byok, horde_key, instruction, base)
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
