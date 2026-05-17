from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path("data/app.db")


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt TEXT NOT NULL,
                negative_prompt TEXT DEFAULT '',
                settings_json TEXT NOT NULL,
                status TEXT NOT NULL,
                error TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                local_path TEXT NOT NULL,
                provider_image_url TEXT,
                width INTEGER,
                height INTEGER,
                seed INTEGER,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                favorite INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(run_id) REFERENCES runs(id)
            )
            """
        )


def create_run(run_id: str, provider: str, model: str, prompt: str, negative_prompt: str, settings: dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO runs (id, provider, model, prompt, negative_prompt, settings_json, status)
            VALUES (?, ?, ?, ?, ?, ?, 'queued')
            """,
            (run_id, provider, model, prompt, negative_prompt, json.dumps(settings, ensure_ascii=False)),
        )


def update_run_status(run_id: str, status: str, error: str | None = None) -> None:
    with get_conn() as conn:
        if status in {"completed", "failed"}:
            conn.execute(
                "UPDATE runs SET status = ?, error = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, error, run_id),
            )
        else:
            conn.execute("UPDATE runs SET status = ?, error = ? WHERE id = ?", (status, error, run_id))


def add_image(
    *,
    run_id: str,
    local_path: str,
    provider_image_url: str | None = None,
    width: int | None = None,
    height: int | None = None,
    seed: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO images (run_id, local_path, provider_image_url, width, height, seed, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, local_path, provider_image_url, width, height, seed, json.dumps(metadata or {}, ensure_ascii=False)),
        )


def get_run(run_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        run = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if not run:
            return None
        images = conn.execute("SELECT * FROM images WHERE run_id = ? ORDER BY id", (run_id,)).fetchall()
        return _shape_run(run, images)


def get_image(image_id: int) -> dict[str, Any] | None:
    with get_conn() as conn:
        image = conn.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
        if not image:
            return None
        return _shape_image(image)


def get_recent_runs(limit: int = 30) -> list[dict[str, Any]]:
    with get_conn() as conn:
        runs = conn.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        shaped: list[dict[str, Any]] = []
        for run in runs:
            images = conn.execute("SELECT * FROM images WHERE run_id = ? ORDER BY id", (run["id"],)).fetchall()
            shaped.append(_shape_run(run, images))
        return shaped


def set_image_favorite(image_id: int, favorite: bool) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE images SET favorite = ? WHERE id = ?", (1 if favorite else 0, image_id))


def delete_image_record(image_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM images WHERE id = ?", (image_id,))


def delete_run_record(run_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM images WHERE run_id = ?", (run_id,))
        conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))


def _shape_run(run: sqlite3.Row, images: list[sqlite3.Row]) -> dict[str, Any]:
    return {
        "id": run["id"],
        "provider": run["provider"],
        "model": run["model"],
        "prompt": run["prompt"],
        "negative_prompt": run["negative_prompt"],
        "settings": json.loads(run["settings_json"] or "{}"),
        "status": run["status"],
        "error": run["error"],
        "created_at": run["created_at"],
        "completed_at": run["completed_at"],
        "images": [_shape_image(image) for image in images],
    }


def _shape_image(image: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": image["id"],
        "run_id": image["run_id"],
        "local_path": image["local_path"],
        "provider_image_url": image["provider_image_url"],
        "width": image["width"],
        "height": image["height"],
        "seed": image["seed"],
        "metadata": json.loads(image["metadata_json"] or "{}"),
        "favorite": bool(image["favorite"]),
        "created_at": image["created_at"],
    }
