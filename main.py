from __future__ import annotations

import os
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from providers.base import GenerationRequest, ProviderError
from providers.fal_provider import FalProvider
from providers.venice_provider import VeniceProvider
from services.db import (
    add_image,
    create_run,
    delete_image_record,
    delete_run_record,
    get_image,
    get_recent_runs,
    get_run,
    init_db,
    set_image_favorite,
    update_run_status,
)
from services.image_store import ImageStore

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")

init_db()
image_store = ImageStore()
executor = ThreadPoolExecutor(max_workers=3)
jobs: dict[str, dict[str, Any]] = {}
jobs_lock = Lock()

DEFAULT_MODELS = {
    "venice": [
        {"id": "fluently-xl", "label": "Fluently XL", "notes": "Good first Venice test model if available on your account."},
        {"id": "hidream", "label": "HiDream", "notes": "May require provider-specific sizing fields."},
        {"id": "qwen-image", "label": "Qwen Image", "notes": "Useful to test after model refresh is added."},
    ],
    "fal": [
        {"id": "fal-ai/flux/schnell", "label": "Flux Schnell", "notes": "Fast Fal starter model."},
        {"id": "fal-ai/flux/dev", "label": "Flux Dev", "notes": "Higher-quality Flux option."},
        {"id": "fal-ai/qwen-image", "label": "Qwen Image", "notes": "General image model."},
        {"id": "fal-ai/fast-sdxl", "label": "Fast SDXL", "notes": "Older SDXL-style fallback."},
    ],
}


def provider_for(name: str):
    if name == "venice":
        return VeniceProvider()
    if name == "fal":
        return FalProvider()
    raise ProviderError(f"Unknown provider: {name}")


def parse_int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def local_path_to_file(local_path: str | None) -> Path | None:
    if not local_path:
        return None
    cleaned = local_path.lstrip("/")
    path = Path(cleaned)
    try:
        path.relative_to(Path("static/generated"))
    except ValueError:
        return None
    return path


def remove_local_file(local_path: str | None) -> None:
    path = local_path_to_file(local_path)
    if path and path.exists() and path.is_file():
        path.unlink()


def build_generation_request(data: dict[str, Any]) -> GenerationRequest:
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        raise ValueError("Prompt is required.")

    provider = (data.get("provider") or "venice").strip().lower()
    model = (data.get("model") or "").strip()
    if not model:
        raise ValueError("Model is required.")

    return GenerationRequest(
        provider=provider,
        model=model,
        prompt=prompt,
        negative_prompt=(data.get("negative_prompt") or "").strip(),
        count=parse_int_or_none(data.get("count")) or 1,
        aspect_ratio=(data.get("aspect_ratio") or "1:1").strip(),
        width=parse_int_or_none(data.get("width")),
        height=parse_int_or_none(data.get("height")),
        seed=parse_int_or_none(data.get("seed")),
        output_format=(data.get("output_format") or "jpeg").strip().lower(),
        safety=bool(data.get("safety", True)),
        raw_settings=data.get("raw_settings") or {},
    )


def enqueue_generation(data: dict[str, Any]) -> dict[str, str]:
    generation_request = build_generation_request(data)
    run_id = uuid.uuid4().hex[:12]

    create_run(
        run_id=run_id,
        provider=generation_request.provider,
        model=generation_request.model,
        prompt=generation_request.prompt,
        negative_prompt=generation_request.negative_prompt,
        settings=data,
    )

    with jobs_lock:
        jobs[run_id] = {"id": run_id, "status": "queued", "error": None}

    executor.submit(run_generation_job, run_id, generation_request)
    return {"job_id": run_id, "run_id": run_id, "status": "queued"}


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/providers")
def api_providers():
    return jsonify(
        {
            "venice": {"configured": bool(os.environ.get("VENICE_API_KEY"))},
            "fal": {"configured": bool(os.environ.get("FAL_KEY"))},
        }
    )


@app.get("/api/models")
def api_models():
    return jsonify(DEFAULT_MODELS)


@app.get("/api/history")
def api_history():
    return jsonify({"runs": get_recent_runs(30)})


@app.get("/api/runs/<run_id>")
def api_run(run_id: str):
    run = get_run(run_id)
    if not run:
        return jsonify({"error": "Run not found."}), 404
    return jsonify({"run": run})


@app.post("/api/generate")
def api_generate():
    data = request.get_json(silent=True) or {}
    try:
        queued = enqueue_generation(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(queued)


@app.post("/api/runs/<run_id>/rerun")
def api_rerun(run_id: str):
    run = get_run(run_id)
    if not run:
        return jsonify({"error": "Run not found."}), 404

    data = dict(run["settings"] or {})
    data.update(
        {
            "provider": run["provider"],
            "model": run["model"],
            "prompt": run["prompt"],
            "negative_prompt": run["negative_prompt"],
        }
    )

    options = request.get_json(silent=True) or {}
    if options.get("vary"):
        data["seed"] = None

    try:
        queued = enqueue_generation(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(queued)


@app.delete("/api/runs/<run_id>")
def api_delete_run(run_id: str):
    run = get_run(run_id)
    if not run:
        return jsonify({"error": "Run not found."}), 404

    for image in run["images"]:
        remove_local_file(image["local_path"])

    delete_run_record(run_id)
    with jobs_lock:
        jobs.pop(run_id, None)
    return jsonify({"ok": True})


@app.post("/api/images/<int:image_id>/favorite")
def api_favorite_image(image_id: int):
    image = get_image(image_id)
    if not image:
        return jsonify({"error": "Image not found."}), 404

    data = request.get_json(silent=True) or {}
    favorite = bool(data.get("favorite", not image["favorite"]))
    set_image_favorite(image_id, favorite)
    return jsonify({"ok": True, "favorite": favorite})


@app.delete("/api/images/<int:image_id>")
def api_delete_image(image_id: int):
    image = get_image(image_id)
    if not image:
        return jsonify({"error": "Image not found."}), 404

    remove_local_file(image["local_path"])
    delete_image_record(image_id)
    return jsonify({"ok": True})


@app.get("/api/jobs/<job_id>")
def api_job(job_id: str):
    run = get_run(job_id)
    with jobs_lock:
        job = jobs.get(job_id, {"id": job_id, "status": run["status"] if run else "unknown", "error": None})
    if not run and job["status"] == "unknown":
        return jsonify({"error": "Job not found."}), 404
    return jsonify({"job": job, "run": run})


def set_job_status(run_id: str, status: str, error: str | None = None) -> None:
    with jobs_lock:
        jobs[run_id] = {"id": run_id, "status": status, "error": error}
    update_run_status(run_id, status, error)


def run_generation_job(run_id: str, generation_request: GenerationRequest) -> None:
    try:
        set_job_status(run_id, "running")
        provider = provider_for(generation_request.provider)
        result = provider.generate(generation_request)

        for index, image in enumerate(result.images, start=1):
            if image.base64_data:
                local_path = image_store.save_base64(
                    data=image.base64_data,
                    provider=generation_request.provider,
                    run_id=run_id,
                    index=index,
                    output_format=generation_request.output_format,
                )
            elif image.source_url:
                local_path = image_store.save_remote(
                    url=image.source_url,
                    provider=generation_request.provider,
                    run_id=run_id,
                    index=index,
                    output_format=generation_request.output_format,
                )
            else:
                continue

            add_image(
                run_id=run_id,
                local_path=local_path,
                provider_image_url=image.source_url,
                width=image.width,
                height=image.height,
                seed=image.seed or generation_request.seed,
                metadata={
                    "image_metadata": image.metadata,
                    "provider_metadata": result.provider_metadata,
                },
            )

        completed_run = get_run(run_id)
        if not completed_run or not completed_run["images"]:
            raise ProviderError("The provider returned a response, but no images were saved.")

        set_job_status(run_id, "completed")
    except Exception as exc:
        error = str(exc)
        print(f"Generation job {run_id} failed: {error}")
        traceback.print_exc()
        set_job_status(run_id, "failed", error)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
