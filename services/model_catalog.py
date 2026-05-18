from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

from services.live_model_cache import load_model_cache

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

RESOLUTION_MP_ESTIMATES = {"1K": 1, "2K": 4, "4K": 8}
VENICE_PRICE_SOURCE = "Venice API pricing page, Media Models > Image Generation."

VENICE_MODELS: list[dict[str, Any]] = [
    {"id": "recraft-v4-pro", "label": "Recraft V4 Pro", "category": "text-to-image", "sizing_mode": "mixed", "pricing": {"unit": "image", "usd": 0.29, "source": VENICE_PRICE_SOURCE}, "notes": "Anonymized image generation model. Venice lists per-image pricing."},
    {"id": "gpt-image-2", "label": "GPT Image 2", "category": "text-to-image", "sizing_mode": "resolution_tier", "supported_resolutions": ["1K", "2K", "4K"], "pricing": {"unit": "resolution_tier", "prices": {"1K": 0.27, "2K": 0.51, "4K": 0.84}, "source": VENICE_PRICE_SOURCE}, "notes": "Resolution-tier image generation model using aspect_ratio plus resolution."},
    {"id": "gpt-image-1-5", "label": "GPT Image 1.5", "category": "text-to-image", "sizing_mode": "mixed", "pricing": {"unit": "image", "usd": 0.26, "source": VENICE_PRICE_SOURCE}, "notes": "Anonymized image generation model. Venice lists per-image pricing."},
    {"id": "nano-banana-pro", "label": "Nano Banana Pro", "category": "text-to-image", "sizing_mode": "resolution_tier", "supported_resolutions": ["1K", "2K", "4K"], "pricing": {"unit": "resolution_tier", "prices": {"1K": 0.18, "2K": 0.23, "4K": 0.35}, "source": VENICE_PRICE_SOURCE}, "notes": "Resolution-tier image generation model using aspect_ratio plus resolution."},
    {"id": "nano-banana-2", "label": "Nano Banana 2", "category": "text-to-image", "sizing_mode": "resolution_tier", "supported_resolutions": ["1K", "2K", "4K"], "pricing": {"unit": "resolution_tier", "prices": {"1K": 0.10, "2K": 0.14, "4K": 0.19}, "source": VENICE_PRICE_SOURCE}, "notes": "Resolution-tier image generation model using aspect_ratio plus resolution."},
    {"id": "qwen-image-2-pro", "label": "Qwen Image 2 Pro", "category": "text-to-image", "sizing_mode": "aspect_ratio", "pricing": {"unit": "image", "usd": 0.10, "source": VENICE_PRICE_SOURCE}, "notes": "Anonymized image generation model. Venice lists per-image pricing."},
    {"id": "wan-2-7-pro-text-to-image", "label": "Wan 2.7 Pro", "category": "text-to-image", "sizing_mode": "mixed", "pricing": {"unit": "image", "usd": 0.09, "source": VENICE_PRICE_SOURCE}, "notes": "Anonymized image generation model. Venice lists per-image pricing."},
    {"id": "flux-2-max", "label": "Flux 2 Max", "category": "text-to-image", "sizing_mode": "mixed", "pricing": {"unit": "image", "usd": 0.09, "source": VENICE_PRICE_SOURCE}, "notes": "Anonymized image generation model. Venice lists per-image pricing."},
    {"id": "grok-imagine-image-quality", "label": "Grok Imagine High Quality", "category": "text-to-image", "sizing_mode": "resolution_tier", "supported_resolutions": ["1K", "2K"], "pricing": {"unit": "resolution_tier", "prices": {"1K": 0.08, "2K": 0.10}, "source": VENICE_PRICE_SOURCE}, "notes": "Private high-quality Grok Imagine image generation model. Venice lists 1K and 2K prices."},
    {"id": "imagineart-1.5-pro", "label": "ImagineArt 1.5 Pro", "category": "text-to-image", "sizing_mode": "mixed", "pricing": {"unit": "image", "usd": 0.06, "source": VENICE_PRICE_SOURCE}, "notes": "Anonymized image generation model. Venice lists per-image pricing."},
    {"id": "qwen-image-2", "label": "Qwen Image 2", "category": "text-to-image", "sizing_mode": "aspect_ratio", "pricing": {"unit": "image", "usd": 0.05, "source": VENICE_PRICE_SOURCE}, "notes": "Aspect-ratio image model. Venice lists per-image pricing."},
    {"id": "recraft-v4", "label": "Recraft V4", "category": "text-to-image", "sizing_mode": "mixed", "pricing": {"unit": "image", "usd": 0.05, "source": VENICE_PRICE_SOURCE}, "notes": "Anonymized image generation model. Venice lists per-image pricing."},
    {"id": "seedream-v4", "label": "Seedream V4.5", "category": "text-to-image", "sizing_mode": "mixed", "pricing": {"unit": "image", "usd": 0.05, "source": VENICE_PRICE_SOURCE}, "notes": "Anonymized image generation model. Venice lists per-image pricing."},
    {"id": "seedream-v5-lite", "label": "Seedream V5 Lite", "category": "text-to-image", "sizing_mode": "mixed", "pricing": {"unit": "image", "usd": 0.05, "source": VENICE_PRICE_SOURCE}, "notes": "Anonymized image generation model. Venice lists per-image pricing."},
    {"id": "flux-2-pro", "label": "Flux 2 Pro", "category": "text-to-image", "sizing_mode": "mixed", "pricing": {"unit": "image", "usd": 0.04, "source": VENICE_PRICE_SOURCE}, "notes": "Anonymized image generation model. Venice lists per-image pricing."},
    {"id": "grok-imagine-image", "label": "Grok Imagine", "category": "text-to-image", "sizing_mode": "resolution_tier", "supported_resolutions": ["1K", "2K"], "pricing": {"unit": "resolution_tier", "prices": {"1K": 0.04, "2K": 0.06}, "source": VENICE_PRICE_SOURCE}, "notes": "Private Grok Imagine image generation model. Venice lists 1K and 2K prices."},
    {"id": "wan-2-7-text-to-image", "label": "Wan 2.7", "category": "text-to-image", "sizing_mode": "mixed", "pricing": {"unit": "image", "usd": 0.04, "source": VENICE_PRICE_SOURCE}, "notes": "Anonymized image generation model. Venice lists per-image pricing."},
    {"id": "wai-Illustrious", "label": "Anime (WAI)", "category": "text-to-image", "sizing_mode": "mixed", "pricing": {"unit": "image", "usd": 0.01, "source": VENICE_PRICE_SOURCE}, "notes": "Private anime-oriented image generation model. Venice lists per-image pricing."},
    {"id": "chroma", "label": "Chroma", "category": "text-to-image", "sizing_mode": "mixed", "pricing": {"unit": "image", "usd": 0.01, "source": VENICE_PRICE_SOURCE}, "notes": "Private image generation model. Venice lists per-image pricing."},
    {"id": "lustify-sdxl", "label": "Lustify SDXL", "category": "text-to-image", "sizing_mode": "pixel", "pricing": {"unit": "image", "usd": 0.01, "source": VENICE_PRICE_SOURCE}, "notes": "Private SDXL image generation model. Venice lists per-image pricing."},
    {"id": "lustify-v7", "label": "Lustify v7", "category": "text-to-image", "sizing_mode": "pixel", "pricing": {"unit": "image", "usd": 0.01, "source": VENICE_PRICE_SOURCE}, "notes": "Private image generation model. Venice lists per-image pricing."},
    {"id": "lustify-v8", "label": "Lustify v8", "category": "text-to-image", "sizing_mode": "pixel", "pricing": {"unit": "image", "usd": 0.01, "source": VENICE_PRICE_SOURCE}, "notes": "Private image generation model. Venice lists per-image pricing."},
    {"id": "venice-sd35", "label": "Venice SD35", "category": "text-to-image", "sizing_mode": "pixel", "pricing": {"unit": "image", "usd": 0.01, "source": VENICE_PRICE_SOURCE}, "notes": "Private pixel-dimension model. The app supplies default dimensions when width/height are left blank."},
    {"id": "z-image-turbo", "label": "Z-Image Turbo", "category": "text-to-image", "sizing_mode": "mixed", "pricing": {"unit": "image", "usd": 0.01, "source": VENICE_PRICE_SOURCE}, "notes": "Private image generation model. Venice lists per-image pricing."},
    {"id": "hunyuan-image-v3", "label": "Hunyuan Image 3.0 (Beta)", "category": "text-to-image", "sizing_mode": "mixed", "pricing": {"unit": "image", "usd": 0.09, "source": VENICE_PRICE_SOURCE}, "notes": "Private beta image generation model. Venice lists per-image pricing."},
    {"id": "bria-bg-remover", "label": "Background Remover", "category": "background-remove", "disabled_for_text_only": True, "sizing_mode": "none", "pricing": {"unit": "image", "usd": 0.03, "source": VENICE_PRICE_SOURCE}, "notes": "Background removal model. Hidden until background-removal workflow exists."},
    {"id": "upscaler", "label": "Image Upscaler", "category": "upscale", "disabled_for_text_only": True, "sizing_mode": "upscale", "pricing": {"unit": "upscale", "prices": {"2x": 0.02, "4x": 0.08}, "source": "Venice API pricing page, Image Generation > Upscaling."}, "notes": "Image upscaling model. Hidden until upscale workflow exists."},
    {"id": "firered-image-edit", "label": "FireRed Image Edit 1.1", "category": "image-to-image", "disabled_for_text_only": True, "sizing_mode": "edit", "pricing": {"unit": "edit", "usd": 0.04, "source": "Venice API pricing page, Image Generation > Editing."}, "notes": "Image edit model. Hidden until editing workflow exists."},
    {"id": "flux-2-max-edit", "label": "Flux 2 Max Edit", "category": "image-to-image", "disabled_for_text_only": True, "sizing_mode": "edit", "pricing": {"unit": "edit", "usd": 0.19, "source": "Venice API pricing page, Image Generation > Editing."}, "notes": "Image edit model. Hidden until editing workflow exists."},
    {"id": "gpt-image-1-5-edit", "label": "GPT Image 1.5 Edit", "category": "image-to-image", "disabled_for_text_only": True, "sizing_mode": "edit", "pricing": {"unit": "edit", "usd": 0.36, "source": "Venice API pricing page, Image Generation > Editing."}, "notes": "Image edit model. Hidden until editing workflow exists."},
    {"id": "gpt-image-2-edit", "label": "GPT Image 2 Edit", "category": "image-to-image", "disabled_for_text_only": True, "sizing_mode": "edit", "pricing": {"unit": "edit", "usd": 0.36, "source": "Venice API pricing page, Image Generation > Editing."}, "notes": "Image edit model. Hidden until editing workflow exists."},
    {"id": "grok-imagine-edit", "label": "Grok Imagine Edit", "category": "image-to-image", "disabled_for_text_only": True, "sizing_mode": "edit", "pricing": {"unit": "edit", "usd": 0.04, "source": "Venice API pricing page, Image Generation > Editing."}, "notes": "Image edit model. Hidden until editing workflow exists."},
    {"id": "grok-imagine-quality-edit", "label": "Grok Imagine High Quality Edit", "category": "image-to-image", "disabled_for_text_only": True, "sizing_mode": "edit", "pricing": {"unit": "edit", "usd": 0.10, "source": "Venice API pricing page, Image Generation > Editing."}, "notes": "Image edit model. Hidden until editing workflow exists."},
    {"id": "nano-banana-2-edit", "label": "Nano Banana 2 Edit", "category": "image-to-image", "disabled_for_text_only": True, "sizing_mode": "edit", "pricing": {"unit": "edit", "usd": 0.10, "source": "Venice API pricing page, Image Generation > Editing."}, "notes": "Image edit model. Hidden until editing workflow exists."},
    {"id": "nano-banana-pro-edit", "label": "Nano Banana Pro Edit", "category": "image-to-image", "disabled_for_text_only": True, "sizing_mode": "edit", "pricing": {"unit": "edit", "usd": 0.18, "source": "Venice API pricing page, Image Generation > Editing."}, "notes": "Image edit model. Hidden until editing workflow exists."},
    {"id": "qwen-edit", "label": "Qwen Edit 2511", "category": "image-to-image", "disabled_for_text_only": True, "sizing_mode": "edit", "pricing": {"unit": "edit", "usd": 0.04, "source": "Venice API pricing page, Image Generation > Editing."}, "notes": "Image edit model. Hidden until editing workflow exists."},
    {"id": "qwen-image-2-edit", "label": "Qwen Image 2 Edit", "category": "image-to-image", "disabled_for_text_only": True, "sizing_mode": "edit", "pricing": {"unit": "edit", "usd": 0.05, "source": "Venice API pricing page, Image Generation > Editing."}, "notes": "Image edit model. Hidden until editing workflow exists."},
    {"id": "qwen-image-2-pro-edit", "label": "Qwen Image 2 Pro Edit", "category": "image-to-image", "disabled_for_text_only": True, "sizing_mode": "edit", "pricing": {"unit": "edit", "usd": 0.10, "source": "Venice API pricing page, Image Generation > Editing."}, "notes": "Image edit model. Hidden until editing workflow exists."},
    {"id": "seedream-v4-edit", "label": "Seedream V4.5 Edit", "category": "image-to-image", "disabled_for_text_only": True, "sizing_mode": "edit", "pricing": {"unit": "edit", "usd": 0.05, "source": "Venice API pricing page, Image Generation > Editing."}, "notes": "Image edit model. Hidden until editing workflow exists."},
    {"id": "seedream-v5-lite-edit", "label": "Seedream V5 Lite Edit", "category": "image-to-image", "disabled_for_text_only": True, "sizing_mode": "edit", "pricing": {"unit": "edit", "usd": 0.05, "source": "Venice API pricing page, Image Generation > Editing."}, "notes": "Image edit model. Hidden until editing workflow exists."},
    {"id": "wan-2-7-pro-edit", "label": "Wan 2.7 Pro Edit", "category": "image-to-image", "disabled_for_text_only": True, "sizing_mode": "edit", "pricing": {"unit": "edit", "usd": 0.09, "source": "Venice API pricing page, Image Generation > Editing."}, "notes": "Image edit model. Hidden until editing workflow exists."},
]

FAL_MODELS: list[dict[str, Any]] = [
    {"id": "fal-ai/flux-2-pro", "label": "FLUX.2 Pro", "category": "text-to-image", "fal_payload_style": "image_size", "pricing": {"unit": "first_mp_then_extra", "first_mp_usd": 0.03, "extra_mp_usd": 0.015, "source": "Fal model page."}, "notes": "Flux 2 Pro is the zero-config production Flux 2 model. Fal bills $0.03 for the first rounded-up megapixel, then $0.015 for each additional rounded-up megapixel."},
    {"id": "fal-ai/flux-2-flex", "label": "FLUX.2 Flex", "category": "text-to-image", "fal_payload_style": "image_size", "pricing": {"unit": "megapixel_rounded_up", "usd": 0.05, "source": "Fal model page."}, "notes": "Flux 2 Flex exposes adjustable inference steps and guidance scale for more control. Fal bills $0.05 per rounded-up megapixel."},
    {"id": "fal-ai/flux/schnell", "label": "FLUX.1 Schnell", "category": "text-to-image", "fal_payload_style": "image_size", "pricing": {"unit": "unknown", "source": "Fal pricing endpoint/model page should be checked for current pricing."}, "notes": "12B flow transformer, high-quality text-to-image in 1–4 steps; Fal marks it suitable for personal and commercial use."},
    {"id": "fal-ai/flux/dev", "label": "FLUX.1 Dev", "category": "text-to-image", "fal_payload_style": "image_size", "pricing": {"unit": "image", "usd": 0.025, "source": "Fal pricing API documentation example; refresh/check Fal for current account pricing."}, "notes": "12B flow transformer for high-quality text-to-image. Fal docs show streaming support."},
    {"id": "fal-ai/flux-pro/v1.1", "label": "FLUX 1.1 Pro", "category": "text-to-image", "fal_payload_style": "image_size", "pricing": {"unit": "megapixel_rounded_up", "usd": 0.04, "source": "Fal model page."}, "notes": "Enhanced FLUX.1 Pro model. Fal bills $0.04 per rounded-up megapixel."},
    {"id": "fal-ai/flux-pro/v1.1-ultra", "label": "FLUX 1.1 Pro Ultra", "category": "text-to-image", "fal_payload_style": "image_size", "pricing": {"unit": "image", "usd": 0.06, "source": "Fal model page."}, "notes": "Ultra supports up to 2K / 4MP output. Fal bills $0.06 per image."},
    {"id": "fal-ai/flux-pro/kontext/text-to-image", "label": "FLUX.1 Kontext Pro Text to Image", "category": "text-to-image", "fal_payload_style": "aspect_ratio", "pricing": {"unit": "image", "usd": 0.04, "source": "Fal model page."}, "notes": "High prompt-following, photorealistic rendering, and typography. Text-to-image endpoint accepts aspect_ratio."},
    {"id": "fal-ai/flux-pro", "label": "FLUX.1 Pro Legacy", "category": "text-to-image", "fal_payload_style": "image_size", "pricing": {"unit": "megapixel_rounded_up", "usd": 0.05, "source": "Fal model page."}, "notes": "Legacy FLUX.1 Pro endpoint. Fal marks it deprecated/no longer supported, so prefer Flux 2 Pro/Flex or Flux 1.1 Pro."},
    {"id": "fal-ai/qwen-image", "label": "Qwen Image", "category": "text-to-image", "fal_payload_style": "image_size", "pricing": {"unit": "megapixel_rounded_up", "usd": 0.02, "source": "Fal model page."}, "notes": "Strong for complex text rendering. Fal bills by rounding images up to the nearest megapixel."},
    {"id": "fal-ai/nano-banana", "label": "Nano Banana", "category": "text-to-image", "fal_payload_style": "aspect_ratio", "pricing": {"unit": "image", "usd": 0.039, "source": "Fal model page."}, "notes": "Google Gemini 2.5 Flash Image / Nano Banana style model. Supports aspect_ratio and output_format."},
    {"id": "fal-ai/bytedance/seedream/v4/text-to-image", "label": "Seedream 4.0 Text to Image", "category": "text-to-image", "fal_payload_style": "image_size", "pricing": {"unit": "image", "usd": 0.03, "source": "Fal model page."}, "notes": "ByteDance Seedream 4.0 integrates image generation and editing in a unified architecture. Text-to-image endpoint accepts image_size, num_images, and max_images."},
    {"id": "openai/gpt-image-2", "label": "GPT Image 2", "category": "text-to-image", "fal_payload_style": "image_size", "pricing": {"unit": "range", "min_usd": 0.01, "max_usd": 0.41, "source": "Fal GPT Image 2 page."}, "notes": "Quality-first model with strong photorealism and text rendering. Fal says pricing ranges from low-quality 1024x768 to high-quality 4K."},
    {"id": "fal-ai/fast-sdxl", "label": "Fast SDXL", "category": "text-to-image", "fal_payload_style": "image_size", "pricing": {"unit": "unknown", "source": "Fal pricing endpoint/model page should be checked for current pricing."}, "notes": "Older SDXL-style fallback. Kept for fast compatibility testing."},
    {"id": "fal-ai/qwen-image-edit", "label": "Qwen Image Edit (later)", "category": "image-to-image", "fal_payload_style": "image_edit", "disabled_for_text_only": True, "pricing": {"unit": "unknown", "source": "Fal pricing endpoint/model page should be checked for current pricing."}, "notes": "Image-editing endpoint with superior text editing capabilities. Needs image upload/input support before it should be generated from the current prompt-only UI."},
    {"id": "fal-ai/flux-pro/kontext", "label": "FLUX.1 Kontext Pro Edit (later)", "category": "image-to-image", "fal_payload_style": "image_edit", "disabled_for_text_only": True, "pricing": {"unit": "image", "usd": 0.04, "source": "Fal model page."}, "notes": "Image editing endpoint. Supports targeted local edits, character consistency, style transfer, and text editing, but needs image upload/input support."},
]

MODEL_CATALOG: dict[str, list[dict[str, Any]]] = {"venice": VENICE_MODELS, "fal": FAL_MODELS}


def get_model_catalog(include_disabled: bool = False) -> dict[str, list[dict[str, Any]]]:
    catalog = merge_live_cache(deepcopy(MODEL_CATALOG))
    if include_disabled:
        return catalog
    return {provider: [model for model in models if not model.get("disabled_for_text_only")] for provider, models in catalog.items()}


def get_model_info(provider: str, model_id: str) -> dict[str, Any] | None:
    catalog = get_model_catalog(include_disabled=True)
    for model in catalog.get(provider, []):
        if model["id"] == model_id:
            return deepcopy(model)
    return None


def merge_live_cache(catalog: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    cache = load_model_cache()
    for provider, provider_cache in ((cache.get("fal") or {}).get("models") or {}).items():
        merge_live_model(catalog, "fal", provider, provider_cache)
    for provider, provider_cache in ((cache.get("venice") or {}).get("models") or {}).items():
        merge_live_model(catalog, "venice", provider, provider_cache)
    return catalog


def merge_live_model(catalog: dict[str, list[dict[str, Any]]], provider: str, model_id: str, live: dict[str, Any]) -> None:
    models = catalog.setdefault(provider, [])
    existing = next((model for model in models if model.get("id") == model_id), None)
    if existing is None:
        existing = {"id": model_id, "label": live.get("label") or model_id, "category": "text-to-image", "notes": live.get("description") or "Discovered from the provider model endpoint.", "pricing": live.get("pricing") or {"unit": "unknown", "source": "live provider cache"}}
        models.append(existing)
    if live.get("label") and existing.get("label") == model_id:
        existing["label"] = live["label"]
    if live.get("pricing") and existing.get("pricing", {}).get("unit") == "unknown":
        existing["pricing"] = live["pricing"]
    if live.get("description") and not existing.get("notes"):
        existing["notes"] = live["description"]
    for key in ("traits", "capabilities", "constraints", "last_refreshed_at", "source"):
        if live.get(key) is not None:
            existing[key] = live[key]
    existing["live_cache"] = {"last_refreshed_at": live.get("last_refreshed_at"), "source": live.get("source")}


def estimate_generation_cost(settings: dict[str, Any]) -> dict[str, Any]:
    provider = (settings.get("provider") or "").lower()
    model_id = settings.get("model") or ""
    model = get_model_info(provider, model_id)
    if not model:
        return {"known": False, "label": "Unknown model", "detail": "No pricing metadata for this model yet."}

    pricing = model.get("pricing") or {}
    count = _parse_int(settings.get("count"), 1)
    resolution = settings.get("resolution") or "1K"
    mp = estimate_megapixels(settings)
    rounded_mp = max(1, math.ceil(mp))
    unit = pricing.get("unit")

    if unit == "image" and pricing.get("usd") is not None:
        total = count * float(pricing["usd"])
        return _known(total, f"${float(pricing['usd']):.4f} per image × {count} image(s)", model, mp)

    if unit == "resolution_tier" and isinstance(pricing.get("prices"), dict):
        prices = pricing["prices"]
        selected_price = prices.get(resolution) or prices.get("1K")
        if selected_price is not None:
            total = count * float(selected_price)
            return _known(total, f"${float(selected_price):.4f} per {resolution or '1K'} image × {count} image(s)", model, mp)
        return {"known": False, "label": f"{model['label']}: resolution price unknown", "detail": f"Known tiers: {', '.join(prices.keys())}", "model": model, "estimated_megapixels": mp}

    if unit == "megapixel_rounded_up" and pricing.get("usd") is not None:
        total = count * rounded_mp * float(pricing["usd"])
        return _known(total, f"${float(pricing['usd']):.4f} per rounded-up MP × {rounded_mp} MP × {count} image(s)", model, mp)

    if unit == "first_mp_then_extra" and pricing.get("first_mp_usd") is not None and pricing.get("extra_mp_usd") is not None:
        per_image = float(pricing["first_mp_usd"]) + max(0, rounded_mp - 1) * float(pricing["extra_mp_usd"])
        total = count * per_image
        return _known(total, f"${float(pricing['first_mp_usd']):.4f} first MP + ${float(pricing['extra_mp_usd']):.4f} per extra rounded-up MP × {count} image(s)", model, mp)

    if unit == "range":
        min_usd = pricing.get("min_usd")
        max_usd = pricing.get("max_usd")
        if min_usd is not None and max_usd is not None:
            return {"known": False, "label": f"{model['label']}: ${float(min_usd):.2f}–${float(max_usd):.2f} per image depending on quality/resolution", "detail": "Exact quality/resolution pricing is not encoded yet.", "model": model, "estimated_megapixels": mp}

    return {"known": False, "label": f"{model['label']}: price unknown", "detail": pricing.get("source") or "No static or live pricing found yet.", "model": model, "estimated_megapixels": mp}


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
    return {"known": True, "total_usd": round(total, 6), "label": f"{model['label']}: about ${total:.4f}", "detail": detail, "model": model, "estimated_megapixels": mp}


def _parse_int(value: Any, fallback: int) -> int:
    try:
        if value in (None, ""):
            return fallback
        return int(value)
    except (TypeError, ValueError):
        return fallback
