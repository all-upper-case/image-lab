from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path
from urllib.parse import urlparse

import requests


DATA_URL_RE = re.compile(r"^data:(?P<mime>[-\w.]+/[-\w.+]+);base64,(?P<data>.+)$", re.DOTALL)


def _safe_ext(content_type: str | None, fallback: str = "jpg") -> str:
    if not content_type:
        return fallback
    guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
    if not guessed:
        return fallback
    ext = guessed.lstrip(".").lower()
    if ext == "jpe":
        return "jpg"
    return ext


def _extension_from_url(url: str, fallback: str = "jpg") -> str:
    path = urlparse(url).path
    suffix = Path(path).suffix.lower().lstrip(".")
    if suffix in {"jpg", "jpeg", "png", "webp", "gif"}:
        return "jpg" if suffix == "jpeg" else suffix
    return fallback


class ImageStore:
    def __init__(self, generated_dir: str | Path = "static/generated") -> None:
        self.generated_dir = Path(generated_dir)
        self.generated_dir.mkdir(parents=True, exist_ok=True)

    def save_base64(self, *, data: str, provider: str, run_id: str, index: int, output_format: str = "jpg") -> str:
        match = DATA_URL_RE.match(data.strip())
        if match:
            content_type = match.group("mime")
            raw_data = match.group("data")
            ext = _safe_ext(content_type, output_format)
        else:
            raw_data = data.strip()
            ext = output_format or "jpg"

        if ext == "jpeg":
            ext = "jpg"

        file_path = self.generated_dir / provider / run_id / f"image_{index}.{ext}"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(base64.b64decode(raw_data))
        return "/" + file_path.as_posix()

    def save_remote(self, *, url: str, provider: str, run_id: str, index: int, output_format: str = "jpg") -> str:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        content_type = response.headers.get("content-type")
        ext = _safe_ext(content_type, _extension_from_url(url, output_format or "jpg"))
        if ext == "jpeg":
            ext = "jpg"
        file_path = self.generated_dir / provider / run_id / f"image_{index}.{ext}"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(response.content)
        return "/" + file_path.as_posix()
