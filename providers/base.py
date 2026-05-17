from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ProviderError(RuntimeError):
    """Raised when an image provider returns an error or unusable response."""


@dataclass
class GenerationRequest:
    provider: str
    model: str
    prompt: str
    negative_prompt: str = ""
    count: int = 1
    aspect_ratio: str = "1:1"
    width: int | None = None
    height: int | None = None
    seed: int | None = None
    output_format: str = "jpeg"
    safety: bool = True
    raw_settings: dict[str, Any] = field(default_factory=dict)

    def normalized_count(self, max_count: int = 4) -> int:
        try:
            parsed = int(self.count)
        except (TypeError, ValueError):
            parsed = 1
        return max(1, min(parsed, max_count))


@dataclass
class GeneratedImage:
    source_url: str | None = None
    base64_data: str | None = None
    content_type: str | None = None
    seed: int | None = None
    width: int | None = None
    height: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResult:
    images: list[GeneratedImage]
    raw_response: dict[str, Any]
    provider_metadata: dict[str, Any] = field(default_factory=dict)
