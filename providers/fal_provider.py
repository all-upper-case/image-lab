from __future__ import annotations

import os
from typing import Any

from providers.base import GeneratedImage, GenerationRequest, GenerationResult, ProviderError
from services.model_catalog import get_model_info

ASPECT_TO_FAL_SIZE = {
    "1:1": "square_hd",
    "16:9": "landscape_16_9",
    "9:16": "portrait_16_9",
    "4:3": "landscape_4_3",
    "3:4": "portrait_4_3",
    "21:9": "landscape_21_9",
    "9:21": "portrait_21_9",
}


def _extract_images(payload: Any) -> list[GeneratedImage]:
    images: list[GeneratedImage] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            url = value.get("url")
            if isinstance(url, str) and url.startswith("http"):
                images.append(
                    GeneratedImage(
                        source_url=url,
                        content_type=value.get("content_type"),
                        width=value.get("width"),
                        height=value.get("height"),
                        seed=value.get("seed"),
                        metadata=value,
                    )
                )
                return
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    return images


class FalProvider:
    name = "fal"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("FAL_KEY")

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self.api_key:
            raise ProviderError("FAL_KEY is not set.")

        # fal-client reads FAL_KEY from the environment.
        os.environ["FAL_KEY"] = self.api_key

        try:
            import fal_client
        except ImportError as exc:
            raise ProviderError("fal-client is not installed. Run: pip install -r requirements.txt") from exc

        model_info = get_model_info("fal", request.model) or {}
        payload_style = model_info.get("fal_payload_style", "image_size")
        if model_info.get("disabled_for_text_only"):
            raise ProviderError(f"{request.model} needs image input/edit support that this UI does not have yet.")

        payload: dict[str, Any] = {
            "prompt": request.prompt,
            "num_images": request.normalized_count(4),
        }

        if payload_style == "aspect_ratio":
            payload["aspect_ratio"] = request.aspect_ratio or "1:1"
            payload["output_format"] = request.output_format or "png"
        else:
            image_size: str | dict[str, int]
            if request.width and request.height:
                image_size = {"width": request.width, "height": request.height}
            else:
                image_size = ASPECT_TO_FAL_SIZE.get(request.aspect_ratio, "square_hd")
            payload["image_size"] = image_size
            payload["output_format"] = request.output_format or "jpeg"

        if request.negative_prompt:
            payload["negative_prompt"] = request.negative_prompt
        if request.seed is not None:
            payload["seed"] = request.seed

        if request.model == "fal-ai/bytedance/seedream/v4/text-to-image":
            payload["max_images"] = max(1, request.normalized_count(4))
            payload["enable_safety_checker"] = request.safety
        elif payload_style == "aspect_ratio" and "nano-banana" in request.model:
            payload["safety_tolerance"] = "4" if request.safety else "6"
        elif request.model.startswith("fal-ai/flux"):
            payload["enable_safety_checker"] = request.safety

        if "enable_safety_checker" in request.raw_settings:
            payload["enable_safety_checker"] = bool(request.raw_settings["enable_safety_checker"])

        for key in ("guidance_scale", "num_inference_steps", "acceleration", "enhance_prompt_mode", "safety_tolerance"):
            if key in request.raw_settings and request.raw_settings[key] not in (None, ""):
                payload[key] = request.raw_settings[key]

        try:
            data = fal_client.subscribe(request.model, arguments=payload, with_logs=True)
        except Exception as exc:
            raise ProviderError(f"Fal request failed: {exc}") from exc

        images = _extract_images(data)
        if not images:
            raise ProviderError(f"Fal response did not contain any recognizable image URLs. Raw response keys: {list(data)[:20] if isinstance(data, dict) else type(data).__name__}")

        return GenerationResult(images=images, raw_response=data, provider_metadata={"request_payload": payload})
