"""Qwen-Image-Edit via a public Hugging Face Space (driven with gradio_client).

Free tier: needs a free HF token (huggingface.co/settings/tokens, "Read" scope).
The Space runs on ZeroGPU — a free token grants a few minutes of GPU per day.

One call handles both app steps, because Qwen-Image-Edit takes an image + a text
instruction and returns an image:
  * generate — "show this necklace worn by an Indian model in a saree"
  * edit     — "change the green stones to red"
"""

from __future__ import annotations

import concurrent.futures as cf
import inspect
import tempfile

from PIL import Image

# Fast first: it reserves ~60s of ZeroGPU per run vs ~240s for the full Space,
# so the free daily budget stretches ~4x further.
SPACES = ["multimodalart/Qwen-Image-Edit-Fast", "Qwen/Qwen-Image-Edit"]
CONNECT_BUDGET = 45   # seconds to establish the client
PREDICT_BUDGET = 150  # seconds for one GPU run
MAX_SIDE = 1024


class HFError(RuntimeError):
    pass


def _downscale(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > MAX_SIDE:
        s = MAX_SIDE / max(w, h)
        img = img.resize((round(w * s), round(h * s)), Image.LANCZOS)
    return img


def _save(img: Image.Image) -> str:
    f = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    _downscale(img).save(f.name)
    return f.name


def _coerce(out) -> Image.Image:
    if isinstance(out, (list, tuple)) and out:
        out = out[0]
    if isinstance(out, dict):
        out = out.get("path") or out.get("url") or out.get("image")
    if isinstance(out, str):
        if out.startswith("http"):
            import requests

            return Image.open(requests.get(out, timeout=60, stream=True).raw).convert("RGB")
        return Image.open(out).convert("RGB")
    if isinstance(out, Image.Image):
        return out.convert("RGB")
    raise HFError(f"Unrecognised Space output: {type(out)!r}")


def _timeout(fn, budget, label):
    with cf.ThreadPoolExecutor(max_workers=1) as ex:
        try:
            return ex.submit(fn).result(timeout=budget)
        except cf.TimeoutError as e:
            raise HFError(f"{label}: timed out after {budget}s") from e


def run(token: str, prompt: str, images: list[Image.Image]) -> Image.Image:
    from gradio_client import Client, handle_file

    if not token:
        raise HFError(
            "No Hugging Face token. Get a free one (Read scope) at "
            "https://huggingface.co/settings/tokens"
        )
    if not images:
        raise HFError("No input image.")

    path = _save(images[0])
    tok_kw = "token" if "token" in inspect.signature(Client.__init__).parameters else "hf_token"
    errors: list[str] = []

    for space in SPACES:
        try:
            client = _timeout(
                lambda: Client(space, verbose=False, **{tok_kw: token}),
                CONNECT_BUDGET,
                f"{space} connect",
            )
        except HFError as e:
            errors.append(str(e))
            continue
        except Exception as e:  # noqa: BLE001
            errors.append(f"{space}: connect {str(e)[:150]}")
            continue

        # Qwen-Image-Edit: predict(image, prompt, seed, randomize_seed,
        #   true_guidance_scale, num_inference_steps, rewrite_prompt) @ /infer.
        # rewrite_prompt=False keeps our engineered prompt intact.
        attempts = (
            dict(image=handle_file(path), prompt=prompt, seed=42, randomize_seed=False,
                 true_guidance_scale=4.0, num_inference_steps=20, rewrite_prompt=False,
                 api_name="/infer"),
            dict(image=handle_file(path), prompt=prompt, api_name="/infer"),
            dict(image=handle_file(path), prompt=prompt),
        )
        for kw in attempts:
            try:
                out = _timeout(lambda kw=kw: client.predict(**kw), PREDICT_BUDGET,
                               f"{space} predict")
                if isinstance(out, (list, tuple)):
                    out = out[0]
                return _coerce(out)
            except HFError as e:
                errors.append(str(e))
            except Exception as e:  # noqa: BLE001
                errors.append(f"{space}: {str(e)[:150]}")

    blob = "\n".join(errors[-6:])
    if "ZeroGPU quota" in blob or "exceeded your" in blob:
        raise HFError(
            "Hugging Face free ZeroGPU budget for today is used up. Try again "
            "tomorrow, or use a token from an account with remaining quota.\n\n" + blob
        )
    raise HFError("Hugging Face Space failed:\n" + blob)
