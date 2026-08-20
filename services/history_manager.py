from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

DEFAULT_HISTORY_PATH = ".fire_compass_history.json"
DEFAULT_MAX_RECORDS = 20


def _history_path(path: str | Path | None = None) -> Path:
    return Path(path or DEFAULT_HISTORY_PATH)


def load_history(
    path: str | Path | None = None,
    limit: int = DEFAULT_MAX_RECORDS,
) -> list[dict]:
    if limit <= 0:
        raise ValueError("履歴件数の上限は1以上にしてください。")

    file_path = _history_path(path)

    if not file_path.exists():
        return []

    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(raw, list):
        return []

    records = [item for item in raw if isinstance(item, dict)]
    records.sort(
        key=lambda item: str(item.get("created_at", "")),
        reverse=True,
    )

    return records[:limit]


def save_history(
    record: dict,
    path: str | Path | None = None,
    max_records: int = DEFAULT_MAX_RECORDS,
) -> dict:
    if not isinstance(record, dict):
        raise ValueError("履歴データはdict形式で指定してください。")

    if max_records <= 0:
        raise ValueError("履歴件数の上限は1以上にしてください。")

    history = load_history(
        path=path,
        limit=max_records,
    )

    saved = dict(record)

    saved.setdefault(
        "id",
        uuid4().hex,
    )

    saved.setdefault(
        "created_at",
        datetime.now(
            timezone.utc
        ).isoformat(
            timespec="seconds"
        ),
    )

    history.insert(0, saved)
    history = history[:max_records]

    file_path = _history_path(path)
    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        json.dumps(
            history,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return saved


def delete_history(
    history_id: str,
    path: str | Path | None = None,
) -> bool:
    if not history_id:
        raise ValueError("削除対象の履歴IDが必要です。")

    history = load_history(
        path=path,
        limit=10000,
    )

    remaining = [
        item
        for item in history
        if item.get("id") != history_id
    ]

    deleted = len(remaining) != len(history)

    if deleted:
        file_path = _history_path(path)

        if remaining:
            file_path.write_text(
                json.dumps(
                    remaining,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        elif file_path.exists():
            file_path.unlink()

    return deleted


def clear_history(
    path: str | Path | None = None,
) -> None:
    file_path = _history_path(path)

    if file_path.exists():
        file_path.unlink()
