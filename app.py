"""Necklace Try-On — prompt builder + result collector (fully free, no API).

The app does everything except the model call:
  1. Upload a necklace image.
  2. It builds an optimised generation prompt for the chosen saree colour. You run
     it in ChatGPT or Google AI Studio (both free in the browser) with the
     necklace attached, then upload the result back.
  3. It builds an optimised edit prompt (default: green stones -> red). You run it
     in the SAME chat, then upload the edited image back.
  4. It shows the input -> generated -> edited strip with download buttons.

No API keys, no quotas, no cost.
"""

from __future__ import annotations

import io

import streamlit as st
from PIL import Image

from prompts import DEFAULT_EDIT_INSTRUCTION, EDIT_PROMPT, GENERATION_PROMPT

st.set_page_config(page_title="Necklace Try-On", page_icon="💎", layout="wide")

SAREE_COLOURS = ["cream and gold", "deep red", "royal blue", "emerald green", "magenta pink"]


def to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def load(upload) -> Image.Image:
    return Image.open(upload).convert("RGB")


def main() -> None:
    st.title("💎 Necklace Try-On")
    st.write(
        "Upload a necklace, get an optimised prompt, run it in a free image tool "
        "(**ChatGPT** or **Google AI Studio**), and upload the result back. "
        "The app handles the upload, the prompt engineering, the edit step and the "
        "final comparison — everything except the one model call."
    )

    with st.sidebar:
        st.header("How to use")
        st.markdown(
            "1. Upload a necklace image.\n"
            "2. **Copy** the generation prompt. Open "
            "[ChatGPT](https://chatgpt.com) or "
            "[Google AI Studio](https://aistudio.google.com), attach the same "
            "necklace image, paste the prompt, run it.\n"
            "3. Upload the generated image back here.\n"
            "4. **Copy** the edit prompt, run it in the *same* chat, upload the "
            "edited image back.\n\n"
            "Recommended model: **Gemini 2.5 Flash Image** (AI Studio) or "
            "**GPT-4o image** (ChatGPT) — both free in the browser."
        )

    for k in ("necklace_img", "generated", "edited"):
        st.session_state.setdefault(k, None)

    # ---- Step 1 --------------------------------------------------------------
    st.subheader("1 · Upload a necklace")
    up = st.file_uploader("Necklace image (JPG / PNG)", type=["jpg", "jpeg", "png"], key="u_neck")
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
    st.download_button(
        "⬇ Download this necklace image (to attach in ChatGPT / AI Studio)",
        to_png_bytes(st.session_state.necklace_img),
        file_name="necklace_input.png",
        mime="image/png",
    )

    # ---- Step 2 --------------------------------------------------------------
    st.subheader("2 · Generate the model shot")
    saree_colour = st.selectbox("Saree colour", SAREE_COLOURS)
    st.caption("Copy this prompt into ChatGPT / AI Studio **with the necklace image attached**:")
    st.code(GENERATION_PROMPT.format(saree_colour=saree_colour), language="text")
    st.link_button("Open ChatGPT ↗", "https://chatgpt.com")
    st.link_button("Open Google AI Studio ↗", "https://aistudio.google.com")

    g = st.file_uploader("Upload the generated image", type=["jpg", "jpeg", "png"], key="u_gen")
    if g is not None:
        st.session_state.generated = load(g)
        st.session_state.edited = None

    if st.session_state.generated is None:
        st.info("Run the generation prompt, then upload the result here to continue.")
        return

    st.image(st.session_state.generated, caption="Generated output", width=400)

    # ---- Step 3 --------------------------------------------------------------
    st.subheader("3 · Edit the stones")
    instruction = st.text_area("Edit instruction", value=DEFAULT_EDIT_INSTRUCTION)
    st.caption("Copy this into the **same chat** (so it edits the image it just made):")
    st.code(EDIT_PROMPT.format(instruction=instruction), language="text")

    e = st.file_uploader("Upload the edited image", type=["jpg", "jpeg", "png"], key="u_edit")
    if e is not None:
        st.session_state.edited = load(e)

    # ---- Result -----------------------------------------------------------
    st.subheader("Result")
    strip = [
        ("Input necklace", st.session_state.necklace_img),
        ("Generated", st.session_state.generated),
        ("Edited", st.session_state.edited),
    ]
    cols = st.columns(3)
    for col, (label, im) in zip(cols, strip):
        if im is not None:
            col.image(im, caption=label, use_container_width=True)
        else:
            col.caption(f"{label} — not yet")

    dl = st.columns(2)
    if st.session_state.generated is not None:
        dl[0].download_button("⬇ Download generated", to_png_bytes(st.session_state.generated),
                              file_name="necklace_on_model.png", mime="image/png")
    if st.session_state.edited is not None:
        dl[1].download_button("⬇ Download edited", to_png_bytes(st.session_state.edited),
                              file_name="necklace_edited.png", mime="image/png")


if __name__ == "__main__":
    main()
