from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

ASPECT_PIXELS_1MP = {
    "1:1": (1024, 1024),
    "16:9": (1365, 768),
    "9:16": (768, 1365),
    "4:3": (1182, 886),
    "3:4": (886, 1182),
    "3:2": (1254, 836),
    "2:3": (836, 1254),
    "21:9": (1565, 671),
    "9:21": (671, 1565),
}

RESOLUTION_MP_ESTIMATES = {
    "1K": 1,
    "2K": 4,
    "4K": 8,
}

MODEL_CATALOG: dict[str, list[dict[str, Any]]] = {
    "venice": [
        {
            "id": "grok-imagine-image",
            "label": "Grok Imagine Image",
            "category": "text-to-image",
            "sizing_mode": "mixed",
            "pricing": {"unit": "unknown", "source": "Venice model pricing should be checked through the live models endpoint for the current account."},
            "notes": "Used in the Venice image-generation docs example. Supports the native Venice image endpoint.",
        },
        {
            "id": "gpt-image-2",
            "label": "GPT Image 2",
            "category": "text-to-image",
            "sizing_mode": "resolution_tier",
            "supported_resolutions": ["1K", "2K", "4K"],
            "pricing": {"unit": "unknown", "source": "Venice model pricing should be checked through the live models endpoint for the current account."},
            "notes": "Venice docs list this as a resolution-tier model using aspect_ratio plus resolution.",
        },
        {
            "id": "nano-banana-pro",
            "label": "Nano Banana Pro",
            "category": "text-to-image",
            "sizing_mode": "resolution_tier",
            "supported_resolutions": ["1K", "2K", "4K"],
            "pricing": {"unit": "unknown", "source": "Venice model pricing should be checked through the live models endpoint for the current account."},
            "notes": "Venice docs list this as a resolution-tier model using aspect_ratio plus resolution.",
        },
        {
            "id": "nano-banana-2",
            "label": "Nano Banana 2",
            "category": "text-to-image",
            "sizing_mode": "resolution_tier",
            "supported_resolutions": ["1K", "2K", "4K"],
            "pricing": {"unit": "unknown", "source": "Venice model pricing should be checked through the live models endpoint for the current account."},
            "notes": "Venice docs list this as a resolution-tier model using aspect_ratio plus resolution.",
        },
        {
            "id": "qwen-image-2",
            "label": "Qwen Image 2",
            "category": "text-to-image",
            "sizing_mode": "aspect_ratio",
            "pricing": {"unit": "unknown", "source": "Venice model pricing should be checked through the live models endpoint for the current account."},
            "notes": "Venice docs list this as an aspect-ratio model.",
        },
        {
            "id": "qwen-image",
            "label": "Qwen Image",
            "category": "text-to-image",
            "sizing_mode": "pixel",
            "pricing": {"unit": "unknown", "source": "Venice model pricing should be checked through the live models endpoint for the current account."},
            "notes": "Venice docs list this as a pixel-dimension model. The app supplies default dimensions when width/height are left blank.",
        },
        {
            "id": "venice-sd35",
            "label": "Venice SD 3.5",
            "category": "text-to-image",
            "sizing_mode": "pixel",
            "pricing": {"unit": "unknown", "source": "Venice model pricing should be checked through the live models endpoint for the current account."},
            "notes": "Venice docs list this as a pixel-dimension model. The app supplies default dimensions when width/height are left blank.",
        },
        {
            "id": "fluently-xl",
            "label": "Fluently XL",
            "category": "text-to-image",
            "sizing_mode": "pixel",
            "pricing": {"unit": "unknown", "source": "Venice model pricing should be checked through the live models endpoint for the current account."},
            "notes": "Starter model kept from the initial app. Confirm availability on your account.",
        },
        {
            "id": "hidream",
            "label": "HiDream",
            "category": "text-to-image",
            "sizing_mode": "mixed",
            "pricing": {"unit": "unknown", "source": "Venice model pricing should be checked through the live models endpoint for the current account."},
            "notes": "Starter model kept from the initial app. Confirm supported sizing in the live model metadata.",
        },
    ],
    "fal": [
        {
            "id": "fal-ai/flux/schnell",
            "label": "FLUX.1 Schnell",
            "category": "text-to-image",
            "fal_payload_style": "image_size",
            "pricing": {"unit": "unknown", "source": "Fal pricing endpoint/model page should be checked for current pricing."},
            "notes": "12B flow transformer, high-quality text-to-image in 1–4 steps; Fal marks it suitable for personal and commercial use.",
        },
        {
            "id": "fal-ai/flux/dev",
            "label": "FLUX.1 Dev",
            "category": "text-to-image",
            "fal_payload_style": "image_size",
            "pricing": {"unit": "image", "usd": 0.025, "source": "Fal pricing API documentation example; refresh/check Fal for current account pricing."},
            "notes": "12B flow transformer for high-quality text-to-image. Fal docs show streaming support.",
        },
        {
            "id": "fal-ai/qwen-image",
            "label": "Qwen Image",
            "category": "text-to-image",
            "fal_payload_style": "image_size",
            "pricing": {"unit": "megapixel_rounded_up", "usd": 0.02, "source": "Fal model page."},
            "notes": "Strong for complex text rendering. Fal bills by rounding images up to the nearest megapixel.",
        },
        {
            "id": "fal-ai/nano-banana",
            "label": "Nano Banana",
            "category": "text-to-image",
            "fal_payload_style": "aspect_ratio",
            "pricing": {"unit": "image", "usd": 0.039, "source": "Fal model page."},
            "notes": "Google Gemini 2.5 Flash Image / Nano Banana style model. Supports aspect_ratio and output_format.",
        },
        {
            "id": "fal-ai/bytedance/seedream/v4/text-to-image",
            "label": "Seedream 4.0 Text to Image",
            "category": "text-to-image",
            "fal_payload_style": "image_size",
            "pricing": {"unit": "image", "usd": 0.03, "source": "Fal model page."},
            "notes": "ByteDance Seedream 4.0 integrates image generation and editing in a unified architecture. Text-to-image endpoint accepts image_size, num_images, and max_images.",
        },
        {
            "id": "fal-ai/flux-pro/kontext/text-to-image",
            "label": "FLUX.1 Kontext Pro Text to Image",
            "category": "text-to-image",
            "fal_payload_style": "aspect_ratio",
            "pricing": {"unit": "image", "usd": 0.04, "source": "Fal model page."},
            "notes": "High prompt-following, photorealistic rendering, and typography. Text-to-image endpoint accepts aspect_ratio.",
        },
        {
            "id": "openai/gpt-image-2",
            "label": "GPT Image 2",
            "category": "text-to-image",
            "fal_payload_style": "image_size",
            "pricing": {"unit": "range", "min_usd": 0.01, "max_usd": 0.41, "source": "Fal GPT Image 2 page."},
            "notes": "Quality-first model with strong photorealism and text rendering. Fal says pricing ranges from low-quality 1024x768 to high-quality 4K.",
        },
        {
            "id": "fal-ai/fast-sdxl",
            "label": "Fast SDXL",
            "category": "text-to-image",
            "fal_payload_style": "image_size",
            "pricing": {"unit": "unknown", "source": "Fal pricing endpoint/model page should be checked for current pricing."},
            "notes": "Older SDXL-style fallback. Kept for fast compatibility testing.",
        },
        {
            "id": "fal-ai/qwen-image-edit",
            "label": "Qwen Image Edit (later)",
            "category": "image-to-image",
            "fal_payload_style": "image_edit",
            "disabled_for_text_only": True,
            "pricing": {"unit": "unknown", "source": "Fal pricing endpoint/model page should be checked for current pricing."},
            "notes": "Image-editing endpoint with superior text editing capabilities. Needs image upload/input support before it should be generated from the current prompt-only UI.",
        },
        {
            "id": "fal-ai/flux-pro/kontext",
            "label": "FLUX.1 Kontext Pro Edit (later)",
            "category": "image-to-image",
            "fal_payload_style": "image_edit",
            "disabled_for_text_only": True,
            "pricing": {"unit": "image", "usd": 0.04, "source": "Fal model page."},
            "notes": "Image editing endpoint. Supports targeted local edits, character consistency, style transfer, and text editing, but needs image upload/input support.",
        },
        {
            "id": "fal-ai/flux-2-flex",
            "label": "FLUX.2 Flex (verify endpoint later)",
            "category": "text-to-image",
            "fal_payload_style": "image_size",
            "disabled_for_text_only": True,
            "pricing": {"unit": "megapixel_rounded_up", "usd": 0.05, "source": "Fal model page/search result; endpoint not verified in this app yet."},
            "notes": "Potential future model. Hidden from the generation dropdown until the exact Fal endpoint and schema are verified.",
        },
    ],
}


def get_model_catalog(include_disabled: bool = False) -> dict[str, list[dict[str, Any]]]:
    catalog = deepcopy(MODEL_CATALOG)
    if include_disabled:
        return catalog
    return {
        provider: [model for model in models if not model.get("disabled_for_text_only")]
        for provider, models in catalog.items()
    }


def get_model_info(provider: str, model_id: str) -> dict[str, Any] | None:
    for model in MODEL_CATALOG.get(provider, []):
        if model["id"] == model_id:
            return deepcopy(model)
    return None


def estimate_generation_cost(settings: dict[str, Any]) -> dict[str, Any]:
    provider = (settings.get("provider") or "").lower()
    model_id = settings.get("model") or ""
    model = get_model_info(provider, model_id)
    if not model:
        return {"known": False, "label": "Unknown model", "detail": "No pricing metadata for this model yet."}

    pricing = model.get("pricing") or {}
    count = _parse_int(settings.get("count"), 1)
    mp = estimate_megapixels(settings)
    unit = pricing.get("unit")

    if unit == "image" and pricing.get("usd") is not None:
        total = count * float(pricing["usd"])
        return _known(total, f"${float(pricing['usd']):.4f} per image × {count} image(s)", model, mp)

    if unit == "megapixel_rounded_up" and pricing.get("usd") is not None:
        rounded_mp = max(1, math.ceil(mp))
        total = count * rounded_mp * float(pricing["usd"])
        return _known(total, f"${float(pricing['usd']):.4f} per rounded-up MP × {rounded_mp} MP × {count} image(s)", model, mp)

    if unit == "range":
        min_usd = pricing.get("min_usd")
        max_usd = pricing.get("max_usd")
        if min_usd is not None and max_usd is not None:
            return {
                "known": False,
                "label": f"{model['label']}: ${float(min_usd):.2f}–${float(max_usd):.2f} per image depending on quality/resolution",
                "detail": "Exact quality/resolution pricing is not encoded yet.",
                "model": model,
                "estimated_megapixels": mp,
            }

    return {
        "known": False,
        "label": f"{model['label']}: price unknown",
        "detail": pricing.get("source") or "No static pricing found yet.",
        "model": model,
        "estimated_megapixels": mp,
    }


def estimate_megapixels(settings: dict[str, Any]) -> float:
    width = _parse_int(settings.get("width"), 0)
    height = _parse_int(settings.get("height"), 0)
    if width > 0 and height > 0:
        return (width * height) / 1_000_000

    resolution = settings.get("resolution")
    if resolution in RESOLUTION_MP_ESTIMATES:
        return float(RESOLUTION_MP_ESTIMATES[resolution])

    aspect = settings.get("aspect_ratio") or "1:1"
    width, height = ASPECT_PIXELS_1MP.get(aspect, ASPECT_PIXELS_1MP["1:1"])
    return (width * height) / 1_000_000


def _known(total: float, detail: str, model: dict[str, Any], mp: float) -> dict[str, Any]:
    return {
        "known": True,
        "total_usd": round(total, 6),
        "label": f"{model['label']}: about ${total:.4f}",
        "detail": detail,
        "model": model,
        "estimated_megapixels": mp,
    }


def _parse_int(value: Any, fallback: int) -> int:
    try:
        if value in (None, ""):
            return fallback
        return int(value)
    except (TypeError, ValueError):
        return fallback
