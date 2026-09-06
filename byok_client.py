"""Optional 'bring your own key' backend.

If the user supplies an API key, generation/editing goes through a top-tier model
at the user's own cost instead of the free AI Horde:
  * key starting with 'AIza'  -> Google Gemini 2.5 Flash Image ("Nano Banana")
  * key starting with 'sk-'   -> OpenAI gpt-image-1

Both take the necklace as a reference image, so fidelity is far higher than the
free path.
"""

from __future__ import annotations

import base64
import io

from PIL import Image


class BYOKError(RuntimeError):
    pass


def _downscale(img: Image.Image, m: int = 1024) -> Image.Image:
    img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > m:
        s = m / max(w, h)
        img = img.resize((round(w * s), round(h * s)), Image.LANCZOS)
    return img


def _gemini(key: str, prompt: str, images: list[Image.Image]) -> Image.Image:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=[prompt, *[_downscale(i) for i in images]],
        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
    )
    if not getattr(resp, "candidates", None):
        raise BYOKError("Gemini returned an empty response.")
    texts = []
    for part in resp.candidates[0].content.parts:
        if getattr(part, "inline_data", None) and part.inline_data.data:
            return Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
        if getattr(part, "text", None):
            texts.append(part.text)
    raise BYOKError(" ".join(texts).strip() or "Gemini returned no image.")


def _openai(key: str, prompt: str, images: list[Image.Image]) -> Image.Image:
    from openai import OpenAI

    client = OpenAI(api_key=key)
    buf = io.BytesIO()
    _downscale(images[0]).save(buf, format="PNG")
    buf.seek(0)
    buf.name = "necklace.png"
    r = client.images.edit(model="gpt-image-1", image=buf, prompt=prompt, size="1024x1024")
    return Image.open(io.BytesIO(base64.b64decode(r.data[0].b64_json))).convert("RGB")


def run(key: str, prompt: str, images: list[Image.Image]) -> Image.Image:
    key = (key or "").strip()
    if not images:
        raise BYOKError("No input image.")
    try:
        if key.startswith("sk-"):
            return _openai(key, prompt, images)
        if key.startswith("AIza"):
            return _gemini(key, prompt, images)
    except BYOKError:
        raise
    except Exception as e:  # noqa: BLE001
        raise BYOKError(str(e)) from e
    raise BYOKError("Key not recognised — expected Gemini (AIza…) or OpenAI (sk-…).")
