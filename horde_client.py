"""AI Horde (stablehorde.net) — free, no card, crowdsourced GPUs.

Supports img2img, so the necklace photo is used as the reference for both steps.
Anonymous key ("0000000000") works but is low priority; a free key from
https://stablehorde.net/register is faster.

Flow: POST /generate/async -> poll /generate/check/<id> -> GET /generate/status/<id>.
Expect minutes per image on the free tier.
"""

from __future__ import annotations

import base64
import io
import time

import requests
from PIL import Image

API = "https://stablehorde.net/api/v2"
ANON_KEY = "0000000000"
CLIENT_AGENT = "necklace-tryon:1.0:assignment"
# SDXL only — SD 1.5 mangles portrait anatomy (double faces, extra limbs).
MODELS = ["AlbedoBase XL (SDXL)", "SDXL 1.0", "Juggernaut XL"]
NEG_PROMPT = (
    "text, watermark, signature, lowres, blurry, jpeg artifacts, deformed, "
    "disfigured, bad anatomy, extra limbs, extra fingers, mutated hands, "
    "two heads, double face, cloned face, cross-eyed, poorly drawn jewelry"
)
MAX_SIDE = 768
POLL_SECS = 6
TIMEOUT_SECS = 900  # 15 min hard cap

# denoising strength per step: high = free to change, low = keep the input
DENOISE = {"generate": 0.72, "edit": 0.42}


class HordeError(RuntimeError):
    pass


def _prep_b64(img: Image.Image) -> tuple[str, int, int]:
    img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > MAX_SIDE:
        s = MAX_SIDE / max(w, h)
        w, h = round(w * s), round(h * s)
        img = img.resize((w, h), Image.LANCZOS)
    w -= w % 64 or 0
    h -= h % 64 or 0
    w, h = max(w, 512), max(h, 512)
    img = img.resize((w, h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=90)
    return base64.b64encode(buf.getvalue()).decode(), w, h


def run(api_key: str, step: str, prompt: str, images: list[Image.Image],
        progress=None) -> Image.Image:
    key = (api_key or "").strip() or ANON_KEY
    headers = {"apikey": key, "Client-Agent": CLIENT_AGENT}

    params = {
        "n": 1,
        "steps": 30,
        "cfg_scale": 7.0,
        "sampler_name": "k_euler_a",
        "karras": True,
        "post_processing": ["GFPGAN"],  # tidy faces
    }
    prompt = f"{prompt} ### {NEG_PROMPT}"  # Horde negative prompt syntax

    if step == "generate":
        # Plain img2img can't turn a necklace-on-white into a person wearing it,
        # so the generation step is text2img: a portrait built from the prompt.
        params.update({"width": 768, "height": 1024})
        payload = {
            "prompt": prompt,
            "models": MODELS,
            "nsfw": False,
            "censor_nsfw": False,
            "r2": True,
            "params": params,
        }
    else:
        if not images:
            raise HordeError("No input image to edit.")
        src_b64, w, h = _prep_b64(images[0])
        params.update({"width": w, "height": h, "denoising_strength": DENOISE.get(step, 0.45)})
        payload = {
            "prompt": prompt,
            "source_image": src_b64,
            "source_processing": "img2img",
            "models": MODELS,
            "nsfw": False,
            "censor_nsfw": False,
            "r2": True,
            "params": params,
        }
    try:
        r = requests.post(f"{API}/generate/async", json=payload, headers=headers, timeout=30)
    except requests.RequestException as e:
        raise HordeError(f"Horde submit failed: {e}") from e
    if r.status_code == 401:
        raise HordeError("Horde rejected the API key.")
    if not r.ok:
        raise HordeError(f"Horde submit {r.status_code}: {r.text[:300]}")
    job_id = r.json().get("id")
    if not job_id:
        raise HordeError(f"Horde: no job id in response: {r.text[:200]}")

    deadline = time.time() + TIMEOUT_SECS
    while time.time() < deadline:
        time.sleep(POLL_SECS)
        try:
            c = requests.get(f"{API}/generate/check/{job_id}", headers=headers, timeout=30).json()
        except requests.RequestException:
            continue
        if c.get("faulted"):
            raise HordeError("Horde job faulted (worker error). Try again.")
        if progress:
            progress(
                f"queue #{c.get('queue_position', '?')}, "
                f"~{c.get('wait_time', '?')}s left, "
                f"{c.get('finished', 0)}/{c.get('finished', 0) + c.get('processing', 0) + c.get('waiting', 0)} done"
            )
        if c.get("done"):
            break
    else:
        raise HordeError(f"Horde timed out after {TIMEOUT_SECS}s — queue too long, try again later.")

    s = requests.get(f"{API}/generate/status/{job_id}", headers=headers, timeout=30).json()
    gens = s.get("generations") or []
    if not gens:
        raise HordeError(f"Horde: no image returned: {str(s)[:200]}")
    img_ref = gens[0].get("img", "")
    if img_ref.startswith("http"):
        data = requests.get(img_ref, timeout=60).content
    else:
        data = base64.b64decode(img_ref)
    return Image.open(io.BytesIO(data)).convert("RGB")
