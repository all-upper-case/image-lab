from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

CACHE_PATH = Path("data/model_cache.json")
FAL_PRICING_URL = "https://api.fal.ai/v1/models/pricing"
VENICE_MODELS_URL = "https://api.venice.ai/api/v1/models"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_model_cache() -> dict[str, Any]:
    if not CACHE_PATH.exists():
        return {"version": 1, "last_refreshed_at": None, "fal": {"models": {}}, "venice": {"models": {}}}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "last_refreshed_at": None, "fal": {"models": {}}, "venice": {"models": {}}}


def save_model_cache(cache: dict[str, Any]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def refresh_model_cache(catalog: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    cache = load_model_cache()
    cache.setdefault("version", 1)
    cache.setdefault("fal", {"models": {}})
    cache.setdefault("venice", {"models": {}})

    results = {
        "started_at": utc_now(),
        "fal": refresh_fal_pricing(cache, catalog.get("fal", [])),
        "venice": refresh_venice_models(cache),
    }

    cache["last_refreshed_at"] = utc_now()
    cache["last_refresh_results"] = results
    save_model_cache(cache)
    return {"cache": cache, "results": results}


def get_model_cache_summary() -> dict[str, Any]:
    cache = load_model_cache()
    return {
        "last_refreshed_at": cache.get("last_refreshed_at"),
        "fal_model_count": len(cache.get("fal", {}).get("models", {})),
        "venice_model_count": len(cache.get("venice", {}).get("models", {})),
        "last_refresh_results": cache.get("last_refresh_results"),
    }


def refresh_fal_pricing(cache: dict[str, Any], fal_models: list[dict[str, Any]]) -> dict[str, Any]:
    api_key = os.environ.get("FAL_KEY")
    result = {"ok": False, "updated": 0, "errors": []}
    if not api_key:
        result["errors"].append("FAL_KEY is not set.")
        return result

    headers = {"Authorization": f"Key {api_key}"}
    fal_cache = cache.setdefault("fal", {"models": {}}).setdefault("models", {})

    for model in fal_models:
        model_id = model.get("id")
        if not model_id or model.get("disabled_for_text_only"):
            continue
        try:
            response = requests.get(FAL_PRICING_URL, headers=headers, params={"endpoint_id": model_id}, timeout=30)
            if response.status_code >= 400:
                result["errors"].append(f"{model_id}: HTTP {response.status_code}: {response.text[:300]}")
                continue
            data = response.json()
            pricing = normalize_fal_pricing(data)
            fal_cache[model_id] = {
                "id": model_id,
                "pricing": pricing,
                "raw_pricing": data,
                "last_refreshed_at": utc_now(),
                "source": "fal /v1/models/pricing",
            }
            result["updated"] += 1
        except Exception as exc:
            result["errors"].append(f"{model_id}: {exc}")

    result["ok"] = result["updated"] > 0
    return result


def normalize_fal_pricing(data: dict[str, Any]) -> dict[str, Any]:
    unit_price = data.get("unit_price") or data.get("price") or data.get("price_per_unit")
    unit = data.get("unit") or data.get("billing_unit") or "unknown"
    currency = data.get("currency") or "USD"

    normalized: dict[str, Any] = {
        "unit": normalize_unit_name(str(unit)),
        "currency": currency,
        "source": "live_fal_pricing_endpoint",
    }

    try:
        if unit_price is not None:
            normalized["usd"] = float(unit_price)
            normalized["unit_price"] = float(unit_price)
    except (TypeError, ValueError):
        normalized["raw_unit_price"] = unit_price

    return normalized


def normalize_unit_name(unit: str) -> str:
    cleaned = unit.lower().replace(" ", "_").replace("-", "_")
    if "megapixel" in cleaned or cleaned in {"mp", "mega_pixel", "mega_pixels"}:
        return "megapixel_rounded_up"
    if "image" in cleaned or cleaned in {"output", "generation"}:
        return "image"
    return cleaned or "unknown"


def refresh_venice_models(cache: dict[str, Any]) -> dict[str, Any]:
    api_key = os.environ.get("VENICE_API_KEY")
    result = {"ok": False, "updated": 0, "errors": []}
    if not api_key:
        result["errors"].append("VENICE_API_KEY is not set.")
        return result

    headers = {"Authorization": f"Bearer {api_key}"}
    venice_cache = cache.setdefault("venice", {"models": {}}).setdefault("models", {})

    try:
        response = requests.get(VENICE_MODELS_URL, headers=headers, params={"type": "image"}, timeout=45)
        if response.status_code >= 400:
            result["errors"].append(f"Venice image models: HTTP {response.status_code}: {response.text[:500]}")
            return result
        data = response.json()
        models = extract_venice_model_list(data)
        for model in models:
            model_id = model.get("id") or model.get("model") or model.get("name")
            if not model_id:
                continue
            venice_cache[model_id] = {
                "id": model_id,
                "label": model.get("name") or model.get("display_name") or model_id,
                "description": model.get("description"),
                "traits": model.get("traits"),
                "capabilities": model.get("capabilities"),
                "constraints": model.get("constraints"),
                "pricing": normalize_venice_pricing(model.get("pricing")),
                "raw_model": model,
                "last_refreshed_at": utc_now(),
                "source": "venice /api/v1/models?type=image",
            }
            result["updated"] += 1
    except Exception as exc:
        result["errors"].append(f"Venice image models: {exc}")

    result["ok"] = result["updated"] > 0
    return result


def extract_venice_model_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("data", "models", "items"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def normalize_venice_pricing(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"unit": "unknown", "source": "live_venice_models_endpoint", "raw": raw}

    normalized = dict(raw)
    normalized.setdefault("source", "live_venice_models_endpoint")
    return normalized
