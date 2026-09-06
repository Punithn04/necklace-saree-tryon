"""Prompt templates for the two steps (generation and stone editing)."""

GENERATION_PROMPT = """\
You are a product photographer for a high-end Indian jewellery brand.

Using the necklace in the attached image, create ONE photorealistic photograph of
an Indian woman wearing THIS EXACT necklace.

Model & styling:
- Indian woman, mid-20s to early 30s, warm natural skin tone, soft studio beauty
  lighting.
- Elegant {saree_colour} silk saree with a matching blouse, hair in a neat low
  bun, subtle traditional makeup, a small bindi.
- Head-and-shoulders / upper-chest crop, slight three-quarter pose, plain softly
  lit studio background. The necklace rests naturally on the collarbone, fully
  visible, unobstructed, and is the clear focal point.

Necklace fidelity (most important):
- Reproduce the necklace EXACTLY as in the attached image: same overall shape,
  same number and arrangement of stones, same stone colours and cuts, same pearl
  drops, same metal tone and filigree pattern. Do NOT redesign, restyle, add,
  remove, or recolour any part of it. Match it like a photograph, not an
  interpretation.

Output: a single realistic photograph. No text, no watermark, no collage.
"""

EDIT_PROMPT = """\
Edit the provided image. {instruction}

Keep everything else identical: the woman's face, pose, skin, hair, saree, the
background, the lighting, and the necklace's shape, metalwork, pearls and every
other stone. Change ONLY what the instruction asks. The result must look like the
same photograph with a localized retouch, not a regenerated scene.

Output: a single realistic photograph. No text, no watermark.
"""

# Used by the free (AI Horde) backend for the generate step, which is text2img:
# there is no reference image, so the necklace is described rather than copied.
GENERATION_PROMPT_NOREF = (
    "photorealistic studio portrait photograph of a beautiful Indian woman in her "
    "late 20s, warm skin tone, soft beauty lighting, wearing an elegant "
    "{saree_colour} silk saree with a matching blouse, hair in a neat low bun, "
    "subtle traditional makeup, small bindi, upper-chest crop, slight three-quarter "
    "pose, plain softly lit studio background. She wears a large ornate Indian "
    "bridal necklace in rose-gold with diamonds, green emerald stones and pearl "
    "drops, resting on her collarbone as the clear focal point. highly detailed, "
    "sharp focus, 85mm lens, no text, no watermark"
)

DEFAULT_EDIT_INSTRUCTION = (
    "Change every green stone in the necklace to a deep red ruby of the same "
    "shape, size and position."
)
