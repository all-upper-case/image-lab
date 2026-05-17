# Model and Pricing Notes

This file records the assumptions behind the Image Lab model catalog. Pricing can change, so treat static prices as helpful estimates rather than a billing guarantee.

## General rules

Fal.ai bills successful model outputs based on the model's billing unit. For image models this is usually either per image or per megapixel. Fal's docs also say prices may change and can be retrieved programmatically through the Platform APIs, including the `/v1/models/pricing` endpoint.

Venice.ai exposes model metadata through `/api/v1/models`, including image models with type filters such as `type=image`. In this app, Venice pricing is currently kept as unknown/static because exact account-current image pricing should be checked from the live Venice model metadata instead of guessed.

## Current catalog behavior

- Text-to-image models are shown in the normal dropdown.
- Image-editing models are documented in the catalog but hidden from the prompt-only dropdown until upload/edit support exists.
- Known Fal per-image models estimate total cost as `price × image count`.
- Known Fal per-megapixel models estimate total cost as `price × rounded-up megapixels × image count`.
- Unknown or range-based pricing is shown as unknown/range instead of inventing an exact value.
- If width and height are blank, the app estimates roughly 1 megapixel for common aspect-ratio presets.
- If a Venice resolution tier is selected, the app estimates 1K as 1 MP, 2K as 4 MP, and 4K as 8 MP for display purposes only.

## Fal models with static pricing currently encoded

| Model | Static pricing currently encoded | Notes |
|---|---:|---|
| `fal-ai/flux/dev` | `$0.025` per image | Price shown in Fal pricing API documentation example. |
| `fal-ai/qwen-image` | `$0.02` per rounded-up megapixel | Strong for complex text rendering; uses `image_size`. |
| `fal-ai/nano-banana` | `$0.039` per image | Aspect-ratio style endpoint. |
| `fal-ai/bytedance/seedream/v4/text-to-image` | `$0.03` per image | Uses `image_size`, `num_images`, and `max_images`. |
| `fal-ai/flux-pro/kontext/text-to-image` | `$0.04` per image | Aspect-ratio style endpoint. |
| `openai/gpt-image-2` | `$0.01–$0.41` per image range | Exact cost depends on quality/resolution; not fully encoded yet. |

## Fal models with unknown pricing currently encoded

| Model | Reason |
|---|---|
| `fal-ai/flux/schnell` | Static price not confirmed during initial research. |
| `fal-ai/fast-sdxl` | Static price not confirmed during initial research. |
| `fal-ai/qwen-image-edit` | Hidden until image edit support exists; static price not confirmed. |

## Venice models currently encoded

| Model | Sizing mode in app | Pricing status |
|---|---|---|
| `grok-imagine-image` | mixed | unknown |
| `gpt-image-2` | resolution tier | unknown |
| `nano-banana-pro` | resolution tier | unknown |
| `nano-banana-2` | resolution tier | unknown |
| `qwen-image-2` | aspect ratio | unknown |
| `qwen-image` | pixel dimensions | unknown |
| `venice-sd35` | pixel dimensions | unknown |
| `fluently-xl` | pixel dimensions | unknown |
| `hidream` | mixed | unknown |

## Things to improve later

- Add a Fal pricing refresh route that calls `/v1/models/pricing` for every cataloged Fal endpoint.
- Add a Venice model refresh route that calls `/api/v1/models?type=image` and merges live metadata into the local catalog.
- Save live pricing snapshots to `data/model_cache.json`.
- Add a model browser/table view so hidden edit/upscale models can be inspected without being selectable for prompt-only generation.
- Add exact GPT Image 2 quality/resolution pricing once the app exposes those settings.
