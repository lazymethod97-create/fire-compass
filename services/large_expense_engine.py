from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

DEFAULT_LARGE_EXPENSE_PATH = ".fire_compass_large_expenses.json"

CATEGORIES = ("旅行", "車", "医療", "その他")

_MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@dataclass
class LargeExpense:
    id: str
    name: str
    category: str
    amount: float
    expected_month: str  # "YYYY-MM"
    memo: str
    created_at: str


def _validate_new_expense(
    name: str,
    category: str,
    amount: float,
    expected_month: str,
) -> None:
    if not (name or "").strip():
        raise ValueError("支出の名称を入力してください。")

    if category not in CATEGORIES:
        raise ValueError(
            f"カテゴリは{', '.join(CATEGORIES)}のいずれかを指定してください。"
        )

    if amount is None or amount < 0:
        raise ValueError("金額は0以上にしてください。")

    if not _MONTH_PATTERN.match((expected_month or "").strip()):
        raise ValueError("予定月はYYYY-MM形式で指定してください。")


def _large_expense_path(path: str | Path | None = None) -> Path:
    return Path(path or DEFAULT_LARGE_EXPENSE_PATH)


def load_large_expenses(
    path: str | Path | None = None,
) -> list[dict]:
    """保存済みの大型支出予定を、予定月の昇順（同月内は登録日時の昇順）で返す。

    このモジュールはfire_engine / action_engine / tax_optimization /
    crash_strategyの計算ロジックには一切関与しない、予定支出の
    記録・集計専用のモジュールである。
    """
    file_path = _large_expense_path(path)

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
        key=lambda item: (
            str(item.get("expected_month", "")),
            str(item.get("created_at", "")),
        )
    )

    return records


def _write_large_expenses(
    records: list[dict],
    path: str | Path | None = None,
) -> None:
    file_path = _large_expense_path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_large_expense(
    name: str,
    category: str,
    amount: float,
    expected_month: str,
    memo: str = "",
    path: str | Path | None = None,
) -> dict:
    """大型支出予定を1件追加する。

    金融計算（資産寿命シミュレーション・現金バッファ・取り崩し優先順位）
    には一切関与しない。予定支出の入力を記録するだけの関数。
    """
    _validate_new_expense(name, category, amount, expected_month)

    record = {
        "id": uuid4().hex,
        "name": name.strip(),
        "category": category,
        "amount": round(float(amount), 2),
        "expected_month": expected_month.strip(),
        "memo": (memo or "").strip(),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    records = load_large_expenses(path=path)
    records.append(record)
    _write_large_expenses(records, path=path)

    return record


def delete_large_expense(
    expense_id: str,
    path: str | Path | None = None,
) -> bool:
    if not expense_id:
        raise ValueError("削除対象の支出IDが必要です。")

    records = load_large_expenses(path=path)
    remaining = [item for item in records if item.get("id") != expense_id]

    deleted = len(remaining) != len(records)

    if deleted:
        _write_large_expenses(remaining, path=path)

    return deleted


def total_for_month(
    expenses: list[dict],
    target_month: str,
) -> float:
    """指定月（YYYY-MM）に予定されている大型支出の合計額を返す。

    今月の安全生活費・取り崩しプランへ「今月分だけ」を反映させるための
    集計専用関数。monthly_budget_engine / withdrawal_engineのロジック
    自体には手を加えない。
    """
    if not isinstance(expenses, list):
        raise ValueError("expensesはリスト形式で指定してください。")

    total = sum(
        float(item.get("amount", 0.0))
        for item in expenses
        if isinstance(item, dict) and item.get("expected_month") == target_month
    )

    return round(total, 2)


def expenses_for_month(
    expenses: list[dict],
    target_month: str,
) -> list[dict]:
    if not isinstance(expenses, list):
        raise ValueError("expensesはリスト形式で指定してください。")

    return [
        item
        for item in expenses
        if isinstance(item, dict) and item.get("expected_month") == target_month
    ]
