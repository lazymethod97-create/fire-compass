from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Sprint 32で追加。「今月使っていい生活費」（judgment_trend_engineが
# 記録している月次のsafe/recommended/max_monthly）に対して、実際に
# その月いくら使ったかを手入力で記録し、突き合わせる。
#
# このモジュールはfire_engine / action_engine / monthly_budget_engine等の
# 計算ロジックには一切関与しない。実支出額の記録と、judgment_trend_engine
# が既に保存している判定結果との突き合わせ（差分計算）のみを行う
# 表示・記録専用のモジュールである。judgment_trend_engine.py側の
# 記録ロジック・データ形式は変更しない。

DEFAULT_ACTUAL_SPENDING_PATH = ".fire_compass_actual_spending.json"

_MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _actual_spending_path(path: str | Path | None = None) -> Path:
    return Path(path or DEFAULT_ACTUAL_SPENDING_PATH)


def _validate_month_and_amount(month: str, actual_amount: float) -> None:
    if not _MONTH_PATTERN.match((month or "").strip()):
        raise ValueError("月はYYYY-MM形式で指定してください。")

    if actual_amount is None or actual_amount < 0:
        raise ValueError("実支出額は0以上にしてください。")


def load_actual_spending(
    path: str | Path | None = None,
) -> list[dict]:
    """記録済みの月次実支出額を、月の昇順で返す。"""
    file_path = _actual_spending_path(path)

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


def _write_actual_spending(
    records: list[dict],
    path: str | Path | None = None,
) -> None:
    file_path = _actual_spending_path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def record_actual_spending(
    month: str,
    actual_amount: float,
    memo: str = "",
    path: str | Path | None = None,
) -> dict:
    """今月の実支出額を1件記録する（同月の既存レコードは上書き）。

    judgment_trend_engine.record_monthly_judgment()と同じ「同月内は
    上書き」の設計に揃えている。judgment_trend_engine側のデータには
    一切書き込まない（別ファイルで独立して管理する）。
    """
    _validate_month_and_amount(month, actual_amount)

    record = {
        "month": month.strip(),
        "actual_amount": round(float(actual_amount), 2),
        "memo": (memo or "").strip(),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    records = load_actual_spending(path=path)
    records = [item for item in records if item.get("month") != record["month"]]
    records.append(record)
    records.sort(key=lambda item: str(item.get("month", "")))

    _write_actual_spending(records, path=path)

    return record


def delete_actual_spending(
    month: str,
    path: str | Path | None = None,
) -> bool:
    if not (month or "").strip():
        raise ValueError("削除対象の月が必要です。")

    records = load_actual_spending(path=path)
    remaining = [item for item in records if item.get("month") != month.strip()]

    deleted = len(remaining) != len(records)

    if deleted:
        _write_actual_spending(remaining, path=path)

    return deleted


@dataclass
class SpendingComparisonRow:
    month: str
    actual_amount: Optional[float] = None
    safe_monthly: Optional[float] = None
    recommended_monthly: Optional[float] = None
    max_monthly: Optional[float] = None
    status: Optional[str] = None
    # 実支出額 − 推奨生活費（プラスなら使い過ぎ、マイナスなら余裕）。
    # judgment_trendの記録がない月はNone。
    variance_vs_recommended: Optional[float] = None
    # 実支出額が安全〜上限生活費のレンジ内に収まっているか。
    # いずれかの記録が欠けている場合はNone（判定不能）。
    within_safe_to_max_range: Optional[bool] = None


def build_spending_comparison(
    actual_records: list[dict],
    judgment_records: list[dict],
) -> list[SpendingComparisonRow]:
    """実支出額の記録（actual_spending_engine）と、月次判定の記録
    （judgment_trend_engine）を月をキーに突き合わせる。

    どちらか一方にしか記録がない月も、判明している範囲の情報のみを
    持つ行として含める（欠けている側の値はNoneのままにし、存在しない
    数値を推測で埋めない）。計算そのものは単純な差分・範囲判定のみで、
    judgment_trend_engine / monthly_budget_engineの判定ロジックには
    一切手を加えない。
    """
    if not isinstance(actual_records, list):
        raise ValueError("actual_recordsはリスト形式で指定してください。")
    if not isinstance(judgment_records, list):
        raise ValueError("judgment_recordsはリスト形式で指定してください。")

    actual_by_month = {
        str(item.get("month", "")): item
        for item in actual_records
        if isinstance(item, dict)
    }
    judgment_by_month = {
        str(item.get("month", "")): item
        for item in judgment_records
        if isinstance(item, dict)
    }

    all_months = sorted(set(actual_by_month) | set(judgment_by_month))

    rows: list[SpendingComparisonRow] = []
    for month in all_months:
        actual_record = actual_by_month.get(month)
        judgment_record = judgment_by_month.get(month)

        actual_amount = (
            actual_record.get("actual_amount") if actual_record else None
        )
        safe_monthly = (
            judgment_record.get("safe_monthly") if judgment_record else None
        )
        recommended_monthly = (
            judgment_record.get("recommended_monthly") if judgment_record else None
        )
        max_monthly = judgment_record.get("max_monthly") if judgment_record else None
        status = judgment_record.get("status") if judgment_record else None

        variance_vs_recommended = None
        if actual_amount is not None and recommended_monthly is not None:
            variance_vs_recommended = round(actual_amount - recommended_monthly, 2)

        within_safe_to_max_range = None
        if (
            actual_amount is not None
            and safe_monthly is not None
            and max_monthly is not None
        ):
            within_safe_to_max_range = safe_monthly <= actual_amount <= max_monthly

        rows.append(
            SpendingComparisonRow(
                month=month,
                actual_amount=actual_amount,
                safe_monthly=safe_monthly,
                recommended_monthly=recommended_monthly,
                max_monthly=max_monthly,
                status=status,
                variance_vs_recommended=variance_vs_recommended,
                within_safe_to_max_range=within_safe_to_max_range,
            )
        )

    return rows
