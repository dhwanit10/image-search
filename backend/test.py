import torch
from diffusers import DiffusionPipeline

pipe = DiffusionPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-schnell",
    torch_dtype=torch.float32
)

pipe.to("cpu")

prompt = "Astronaut in a jungle, cold color palette, muted colors, detailed"

image = pipe(
    prompt,
    num_inference_steps=4,
    height=512,
    width=512
).images[0]

image.save("astronaut.png")