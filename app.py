"""Necklace Try-On — Streamlit prototype.

Upload a necklace image -> generate a photo of the same necklace worn by an
Indian model in a saree -> edit the stones on that image (e.g. green -> red).
All image work runs on Cloudflare Workers AI (SDXL img2img), free tier.
"""

from __future__ import annotations

import io

import streamlit as st
from PIL import Image

from cf_client import CFError, run
from prompts import DEFAULT_EDIT_INSTRUCTION, EDIT_PROMPT, GENERATION_PROMPT

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


def get_creds() -> tuple[str | None, str | None]:
    acct = _secret("CF_ACCOUNT_ID")
    token = _secret("CF_API_TOKEN")
    with st.sidebar:
        st.header("Setup")
        if acct and token:
            st.success("Using Cloudflare creds from app secrets.")
        else:
            acct = st.text_input("Cloudflare Account ID", value=acct or "") or None
            token = st.text_input("Cloudflare API token", value=token or "", type="password") or None
        st.caption("Model: SDXL img2img on Cloudflare Workers AI (free — 10,000 runs/day).")
        st.caption(
            "Free account: Account ID from the Workers & Pages page; API token from "
            "My Profile → API Tokens → 'Workers AI' template."
        )
    return acct, token


def generate(acct, token, step, prompt, images, label):
    with st.spinner(f"{label} on Cloudflare Workers AI…"):
        try:
            return run(acct, token, step, prompt, images)
        except CFError as e:
            st.error(str(e))
            return None


def main() -> None:
    st.title("💎 Necklace Try-On")
    st.write(
        "Upload a necklace image and generate a realistic photo of the same "
        "necklace worn by an Indian model in a saree — then tweak the stones."
    )

    acct, token = get_creds()
    ready = bool(acct and token)
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
    if st.button("Generate", type="primary", disabled=not ready):
        img = generate(
            acct, token, "generate",
            GENERATION_PROMPT.format(saree_colour=saree_colour),
            [st.session_state.necklace_img],
            "Generating",
        )
        if img is not None:
            st.session_state.generated, st.session_state.edited = img, None
    if not ready:
        st.warning("Add your Cloudflare Account ID and API token in the sidebar.")

    if st.session_state.generated is None:
        return
    st.image(st.session_state.generated, caption="Generated output", width=400)
    st.download_button("Download generated", to_png_bytes(st.session_state.generated),
                       file_name="necklace_on_model.png", mime="image/png")

    # ---- Step 3: edit ------------------------------------------------------
    st.subheader("3 · Edit the stones")
    instruction = st.text_area("Edit instruction", value=DEFAULT_EDIT_INSTRUCTION)
    if st.button("Apply edit", disabled=not ready):
        base = st.session_state.edited or st.session_state.generated
        img = generate(acct, token, "edit", EDIT_PROMPT.format(instruction=instruction),
                       [base], "Editing")
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
