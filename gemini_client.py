"""Wrapper around Gemini 2.5 Flash Image ("Nano Banana").

One call does both jobs — generation and editing — because the model takes
image(s) + a text instruction and returns an image.

Free tier note: the image model returns `RESOURCE_EXHAUSTED` / `limit: 0` when
the request originates from some regions (India, EU, UK). Running the app from a
US host (e.g. Streamlit Community Cloud) uses the free quota normally.
"""

from __future__ import annotations

import io

from google import genai
from google.genai import types
from PIL import Image

MODEL = "gemini-2.5-flash-image"
MAX_SIDE = 1024


class GeminiError(RuntimeError):
    pass


def _downscale(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > MAX_SIDE:
        s = MAX_SIDE / max(w, h)
        img = img.resize((round(w * s), round(h * s)), Image.LANCZOS)
    return img


def _extract(resp):
    if not getattr(resp, "candidates", None):
        return None, ""
    texts = []
    for part in resp.candidates[0].content.parts:
        if getattr(part, "inline_data", None) and part.inline_data.data:
            return Image.open(io.BytesIO(part.inline_data.data)).convert("RGB"), ""
        if getattr(part, "text", None):
            texts.append(part.text)
    return None, "\n".join(texts)


def run(api_key: str, prompt: str, images: list[Image.Image]) -> Image.Image:
    """Send `prompt` + `images` to Gemini, return the generated image."""
    if not api_key:
        raise GeminiError("No Gemini API key set.")
    client = genai.Client(api_key=api_key)
    parts = [prompt, *[_downscale(i) for i in images]]
    try:
        resp = client.models.generate_content(
            model=MODEL,
            contents=parts,
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
        )
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        if "RESOURCE_EXHAUSTED" in msg or "limit: 0" in msg:
            raise GeminiError(
                "Gemini free tier returned limit: 0 — this happens outside the US. "
                "Deploy the app on a US host (Streamlit Community Cloud) and it works."
            ) from e
        raise GeminiError(msg) from e
    img, text = _extract(resp)
    if img is None:
        raise GeminiError(text.strip() or "Gemini returned no image; try rephrasing the prompt.")
    return img
