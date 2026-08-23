from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG_PATH = ".fire_compass_events.log"
DEFAULT_MAX_EVENTS = 500
VALID_LEVELS = {"INFO", "WARNING", "ERROR"}
CSV_FIELDNAMES = ["timestamp", "level", "event_type", "message"]


def _read_entries(file_path: Path) -> list[dict]:
    if not file_path.exists():
        return []

    try:
        raw_text = file_path.read_text(encoding="utf-8")
    except OSError:
        return []

    entries: list[dict] = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            entries.append(parsed)

    return entries


def log_event(
    event_type: str,
    message: str,
    level: str = "INFO",
    path: str | Path | None = None,
    max_events: int = DEFAULT_MAX_EVENTS,
) -> dict | None:
    """アプリの動作イベント・エラーをローカルのログファイルへ記録する。

    金融計算やAIアドバイスのロジックには一切関与しない。
    ログの記録に失敗しても例外を外部へ送出せず、アプリ本体の動作を止めない。
    """
    if not event_type:
        raise ValueError("event_typeは必須です。")

    if max_events <= 0:
        raise ValueError("max_eventsは1以上にしてください。")

    normalized_level = (level or "INFO").strip().upper()
    if normalized_level not in VALID_LEVELS:
        normalized_level = "INFO"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "level": normalized_level,
        "event_type": str(event_type),
        # APIキー等の秘密値が誤って渡された場合の被害を抑えるため、長さを制限する。
        "message": str(message)[:500],
    }

    file_path = Path(path or DEFAULT_LOG_PATH)

    try:
        events = _read_entries(file_path)
        events.append(entry)
        events = events[-max_events:]

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(
            "\n".join(json.dumps(item, ensure_ascii=False) for item in events)
            + "\n",
            encoding="utf-8",
        )
    except OSError:
        return None

    return entry


def load_events(
    path: str | Path | None = None,
    limit: int = DEFAULT_MAX_EVENTS,
    level: str | None = None,
) -> list[dict]:
    """記録済みのイベントを新しい順に返す。"""
    if limit <= 0:
        raise ValueError("limitは1以上にしてください。")

    file_path = Path(path or DEFAULT_LOG_PATH)
    entries = _read_entries(file_path)

    if level:
        normalized = level.strip().upper()
        entries = [item for item in entries if item.get("level") == normalized]

    # ファイルには記録した順（古い→新しい）で保存されているため、
    # そのまま反転すれば「同一秒内の複数イベント」でも新しい順になる。
    entries = list(reversed(entries))

    return entries[:limit]


def filter_events(
    events: list[dict],
    keyword: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """イベント一覧をキーワード・期間で絞り込む。

    金融計算やAIアドバイスのロジックには一切関与しない、表示専用の絞り込み関数。
    load_events()の戻り値（レベル絞り込み・新しい順ソート済み）に対して
    追加でキーワード検索・期間指定を適用することを想定している。
    log_event / load_events / clear_eventsのロジックは変更しない。

    Args:
        events: load_events()等で取得したイベントのリスト。
        keyword: event_typeまたはmessageに部分一致（大文字小文字を区別しない）
            するキーワード。空文字・Noneの場合はキーワード絞り込みを行わない。
        start_date: "YYYY-MM-DD"形式の開始日（この日を含む）。
            timestampの先頭10文字（日付部分）と文字列比較する。
        end_date: "YYYY-MM-DD"形式の終了日（この日を含む）。
    """
    if not isinstance(events, list):
        raise ValueError("eventsはリスト形式で指定してください。")

    filtered = [event for event in events if isinstance(event, dict)]

    normalized_keyword = (keyword or "").strip().lower()
    if normalized_keyword:
        filtered = [
            event
            for event in filtered
            if normalized_keyword in str(event.get("event_type", "")).lower()
            or normalized_keyword in str(event.get("message", "")).lower()
        ]

    if start_date:
        start_str = str(start_date)[:10]
        filtered = [
            event
            for event in filtered
            if str(event.get("timestamp", ""))[:10] >= start_str
        ]

    if end_date:
        end_str = str(end_date)[:10]
        filtered = [
            event
            for event in filtered
            if str(event.get("timestamp", ""))[:10] <= end_str
        ]

    return filtered


def clear_events(path: str | Path | None = None) -> None:
    """記録済みのログファイルを削除する。"""
    file_path = Path(path or DEFAULT_LOG_PATH)

    if file_path.exists():
        file_path.unlink()


def export_events_to_csv(events: list[dict]) -> str:
    """イベント一覧をCSV文字列へ変換する。

    金融計算やAIアドバイスのロジックには一切関与しない。
    load_eventsの戻り値（timestamp / level / event_type / message）を
    そのままCSVの列として書き出すだけの整形専用の関数。
    """
    if not isinstance(events, list):
        raise ValueError("eventsはリスト形式で指定してください。")

    buffer = io.StringIO()
    # Excel（Windows）で文字化けしないよう、改行はCRLF・BOM付きUTF-8相当で出力する。
    writer = csv.DictWriter(
        buffer,
        fieldnames=CSV_FIELDNAMES,
        extrasaction="ignore",
        lineterminator="\r\n",
    )
    writer.writeheader()

    for event in events:
        if not isinstance(event, dict):
            continue
        writer.writerow(
            {
                "timestamp": event.get("timestamp", ""),
                "level": event.get("level", ""),
                "event_type": event.get("event_type", ""),
                "message": event.get("message", ""),
            }
        )

    return "\ufeff" + buffer.getvalue()


def events_export_filename(level: str | None = None) -> str:
    """CSVダウンロード用のファイル名を生成する。"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if level:
        normalized = level.strip().upper()
        if normalized in VALID_LEVELS:
            return f"fire_compass_events_{normalized}_{timestamp}.csv"

    return f"fire_compass_events_{timestamp}.csv"
