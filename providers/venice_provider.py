from __future__ import annotations

import os
import re
from typing import Any

import requests

from providers.base import GeneratedImage, GenerationRequest, GenerationResult, ProviderError

VENICE_IMAGE_GENERATE_URL = "https://api.venice.ai/api/v1/image/generate"
BASE64_RE = re.compile(r"^[A-Za-z0-9+/=\s]+$")


def _looks_like_base64_image(value: str) -> bool:
    stripped = value.strip()
    if stripped.startswith("data:image/"):
        return True
    return len(stripped) > 400 and bool(BASE64_RE.match(stripped))


def _extract_images(payload: Any) -> list[GeneratedImage]:
    images: list[GeneratedImage] = []

    def walk(value: Any, parent_key: str = "") -> None:
        if isinstance(value, dict):
            url = value.get("url") or value.get("image_url")
            b64 = value.get("b64_json") or value.get("base64") or value.get("base64_data")
            image_value = value.get("image")
            if isinstance(url, str) and url.startswith("http"):
                images.append(
                    GeneratedImage(
                        source_url=url,
                        width=value.get("width"),
                        height=value.get("height"),
                        seed=value.get("seed"),
                        metadata=value,
                    )
                )
                return
            if isinstance(b64, str) and _looks_like_base64_image(b64):
                images.append(
                    GeneratedImage(
                        base64_data=b64,
                        width=value.get("width"),
                        height=value.get("height"),
                        seed=value.get("seed"),
                        metadata=value,
                    )
                )
                return
            if isinstance(image_value, str) and _looks_like_base64_image(image_value):
                images.append(
                    GeneratedImage(
                        base64_data=image_value,
                        width=value.get("width"),
                        height=value.get("height"),
                        seed=value.get("seed"),
                        metadata=value,
                    )
                )
                return
            for key, item in value.items():
                walk(item, key)
        elif isinstance(value, list):
            for item in value:
                walk(item, parent_key)
        elif isinstance(value, str) and parent_key in {"images", "image", "data", "b64_json", "base64"}:
            if _looks_like_base64_image(value):
                images.append(GeneratedImage(base64_data=value))

    walk(payload)
    return images


class VeniceProvider:
    name = "venice"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("VENICE_API_KEY")

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not self.api_key:
            raise ProviderError("VENICE_API_KEY is not set.")

        payload: dict[str, Any] = {
            "model": request.model,
            "prompt": request.prompt,
            "format": request.output_format or "jpeg",
            "return_binary": False,
            "variants": request.normalized_count(4),
            "safe_mode": request.safety,
        }

        if request.negative_prompt:
            payload["negative_prompt"] = request.negative_prompt
        if request.seed is not None:
            payload["seed"] = request.seed
        if request.width and request.height:
            payload["width"] = request.width
            payload["height"] = request.height
        elif request.aspect_ratio:
            payload["aspect_ratio"] = request.aspect_ratio

        # Allow advanced fields later without changing the UI first.
        for key in ("cfg_scale", "steps", "style_preset", "resolution", "lora_strength"):
            if key in request.raw_settings and request.raw_settings[key] not in (None, ""):
                payload[key] = request.raw_settings[key]

        response = requests.post(
            VENICE_IMAGE_GENERATE_URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=180,
        )
        if response.status_code >= 400:
            raise ProviderError(f"Venice returned HTTP {response.status_code}: {response.text[:2000]}")

        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderError(f"Venice returned non-JSON response: {response.text[:500]}") from exc

        images = _extract_images(data)
        if not images:
            raise ProviderError(f"Venice response did not contain any recognizable images. Raw response keys: {list(data)[:20]}")

        return GenerationResult(images=images, raw_response=data, provider_metadata={"request_payload": payload})
