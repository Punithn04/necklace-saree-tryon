"""Cloudflare Workers AI — free-tier image editing (SDXL img2img).

Free tier: 10,000 Neurons/day, no card. Needs a free Cloudflare account:
  * Account ID — dash.cloudflare.com -> Workers & Pages (shown in the right rail),
                 or Workers AI -> "Use REST API".
  * API token  — dash -> My Profile -> API Tokens -> Create Token
                 -> use the "Workers AI" template -> Create.

One call serves both steps; `strength` controls how far the model may move from
the input image (small for a stone recolour, large for placing it on a model).
"""

from __future__ import annotations

import base64
import io

import requests
from PIL import Image

MODEL = "@cf/stabilityai/stable-diffusion-xl-base-1.0"
MAX_SIDE = 1024
TIMEOUT = 120
NEG = (
    "text, watermark, signature, logo, lowres, blurry, jpeg artifacts, deformed, "
    "disfigured, bad anatomy, extra limbs, extra fingers, mutated hands, cropped, "
    "poorly drawn jewelry, melted jewelry"
)
# How much the model may deviate from the input image, per step.
STRENGTH = {"generate": 0.85, "edit": 0.45}


class CFError(RuntimeError):
    pass


def _prep(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > MAX_SIDE:
        s = MAX_SIDE / max(w, h)
        img = img.resize((round(w * s), round(h * s)), Image.LANCZOS)
    return img


def _b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def run(
    account_id: str, api_token: str, step: str, prompt: str, images: list[Image.Image]
) -> Image.Image:
    if not account_id or not api_token:
        raise CFError("Set your Cloudflare Account ID and API token in the sidebar.")
    if not images:
        raise CFError("No input image.")

    src = _prep(images[0])
    b64 = _b64(src)
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{MODEL}"
    headers = {"Authorization": f"Bearer {api_token}"}
    base = {
        "prompt": prompt,
        "negative_prompt": NEG,
        "strength": STRENGTH.get(step, 0.6),
        "guidance": 7.5,
        "num_steps": 20,
    }
    # Some deployments want `image_b64` (string), others `image` (byte array).
    payloads = [
        {**base, "image_b64": b64},
        {**base, "image": list(base64.b64decode(b64))},
    ]

    last = ""
    for payload in payloads:
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        except requests.RequestException as e:
            raise CFError(f"Cloudflare request failed: {e}") from e

        ctype = r.headers.get("content-type", "")
        if r.ok and ctype.startswith("image/"):
            return Image.open(io.BytesIO(r.content)).convert("RGB")
        try:
            data = r.json()
        except ValueError:
            last = f"{r.status_code}: {r.text[:300]}"
            continue
        result = data.get("result")
        if data.get("success") and isinstance(result, dict) and result.get("image"):
            return Image.open(io.BytesIO(base64.b64decode(result["image"]))).convert("RGB")
        last = str(data.get("errors") or data)[:400]

    if "10000" in last or "quota" in last.lower() or "limit" in last.lower():
        raise CFError(f"Cloudflare free daily limit reached. Try again tomorrow.\n{last}")
    raise CFError(f"Cloudflare error: {last}")
