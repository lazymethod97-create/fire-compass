from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_JUDGMENT_TREND_PATH = ".fire_compass_judgment_trend.json"

_MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

STATUSES = ("green", "yellow", "red")


def _judgment_trend_path(path: str | Path | None = None) -> Path:
    return Path(path or DEFAULT_JUDGMENT_TREND_PATH)


def _validate_record(
    month: str,
    safe_monthly: float,
    recommended_monthly: float,
    max_monthly: float,
    status: str,
) -> None:
    if not _MONTH_PATTERN.match((month or "").strip()):
        raise ValueError("月はYYYY-MM形式で指定してください。")

    numeric_values = (safe_monthly, recommended_monthly, max_monthly)
    if any(value is None or value < 0 for value in numeric_values):
        raise ValueError("生活費の金額は0以上にしてください。")

    if status not in STATUSES:
        raise ValueError(
            f"statusは{', '.join(STATUSES)}のいずれかを指定してください。"
        )


def load_judgment_trend(
    path: str | Path | None = None,
) -> list[dict]:
    """記録済みの月次FIRE判定を、月の昇順で返す。

    このモジュールはfire_engine / action_engine / monthly_budget_engine等の
    計算ロジックには一切関与しない。calculate_monthly_budget()が算出した
    結果を月単位で記録・取得するだけの、履歴トレンド表示専用モジュールである。
    """
    file_path = _judgment_trend_path(path)

    if not file_path.exists():
        return []

    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(raw, list):
        return []

    records = [item for item in raw if isinstance(item, dict)]
    records.sort(key=lambda item: str(item.get("month", "")))

    return records


def _write_judgment_trend(
    records: list[dict],
    path: str | Path | None = None,
) -> None:
    file_path = _judgment_trend_path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def record_monthly_judgment(
    month: str,
    safe_monthly: float,
    recommended_monthly: float,
    max_monthly: float,
    status: str,
    binding_safe_factor_reason: str = "",
    path: str | Path | None = None,
) -> dict:
    """今月のFIRE判定結果を1件記録する（同月の既存レコードは上書き）。

    シミュレーションを実行するたびに呼び出される想定で、同じ月内に
    複数回実行された場合は最新の結果で上書きする（同月内で複数レコードが
    残ることはない）。月をまたいだ過去の記録はそのまま保持される。

    calculate_monthly_budget()の出力をそのまま記録するだけで、
    生活費・判定そのものの再計算は一切行わない。
    """
    _validate_record(month, safe_monthly, recommended_monthly, max_monthly, status)

    record = {
        "month": month.strip(),
        "safe_monthly": round(float(safe_monthly), 2),
        "recommended_monthly": round(float(recommended_monthly), 2),
        "max_monthly": round(float(max_monthly), 2),
        "status": status,
        "binding_safe_factor_reason": binding_safe_factor_reason or "",
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    records = load_judgment_trend(path=path)
    records = [item for item in records if item.get("month") != record["month"]]
    records.append(record)
    records.sort(key=lambda item: str(item.get("month", "")))

    _write_judgment_trend(records, path=path)

    return record
