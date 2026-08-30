from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

DEFAULT_LARGE_EXPENSE_PATH = ".fire_compass_large_expenses.json"

CATEGORIES = ("旅行", "車", "医療", "その他")

_MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

# Sprint 26で追加。1件の大型支出を、予定月から連続するNヶ月に
# 均等分散して計上できるようにする（例: 90万円の旅行費用を3ヶ月に
# 分けて計上）。1（分散なし・従来通り単月計上）が既存呼び出しとの
# 後方互換のデフォルト値。
DEFAULT_DISTRIBUTION_MONTHS = 1


def _validate_new_expense(
    name: str,
    category: str,
    amount: float,
    expected_month: str,
    distribution_months: int,
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

    if (
        distribution_months is None
        or not isinstance(distribution_months, int)
        or isinstance(distribution_months, bool)
        or distribution_months < 1
    ):
        raise ValueError("分散月数は1以上の整数にしてください。")


def _large_expense_path(path: str | Path | None = None) -> Path:
    return Path(path or DEFAULT_LARGE_EXPENSE_PATH)


def _add_months(month_str: str, offset: int) -> str:
    """"YYYY-MM"にoffsetヶ月を加算した"YYYY-MM"を返す（年またぎ対応）。"""
    year, month = (int(part) for part in month_str.split("-"))
    total_months = year * 12 + (month - 1) + offset
    new_year, new_month = divmod(total_months, 12)
    return f"{new_year:04d}-{new_month + 1:02d}"


def _month_amounts(
    amount: float,
    expected_month: str,
    distribution_months: int,
) -> dict[str, float]:
    """1件の大型支出を分散月数ぶんの月別金額に分割する。

    均等に割り切れない端数は、できるだけ均等になるよう各月へ1銭単位
    （0.01万円単位）で分散する（前方の月から順に1単位ずつ多く割り当てる）。
    分散した金額の合計は必ずamountの元の丸め額（小数点2桁）と一致する。
    """
    distribution_months = max(int(distribution_months or 1), 1)

    total_cents = round(float(amount) * 100)
    base_cents, remainder_cents = divmod(total_cents, distribution_months)

    months = [_add_months(expected_month, i) for i in range(distribution_months)]

    result: dict[str, float] = {}
    for index, month in enumerate(months):
        cents = base_cents + (1 if index < remainder_cents else 0)
        # 同じ支出が複数分散区間にまたがることはない前提だが、念のため加算にする。
        result[month] = round(result.get(month, 0.0) + cents / 100.0, 2)

    return result


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
    distribution_months: int = DEFAULT_DISTRIBUTION_MONTHS,
    path: str | Path | None = None,
) -> dict:
    """大型支出予定を1件追加する。

    金融計算（資産寿命シミュレーション・現金バッファ・取り崩し優先順位）
    には一切関与しない。予定支出の入力を記録するだけの関数。

    distribution_months（Sprint 26で追加、省略可能・デフォルト1）は、
    amountをexpected_monthから連続する何ヶ月に均等分散して計上するか。
    1（デフォルト）を指定した場合は既存呼び出しと完全に同じ挙動になる。
    """
    _validate_new_expense(name, category, amount, expected_month, distribution_months)

    record = {
        "id": uuid4().hex,
        "name": name.strip(),
        "category": category,
        "amount": round(float(amount), 2),
        "expected_month": expected_month.strip(),
        "memo": (memo or "").strip(),
        "distribution_months": int(distribution_months),
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
    """指定月（YYYY-MM）に計上される大型支出の合計額を返す。

    Sprint 26より、distribution_monthsが2以上の支出は、分散区間に
    target_monthが含まれる場合にその月の按分額のみを計上する
    （distribution_monthsが未設定・1の既存データは従来通り単月全額）。

    今月の安全生活費・取り崩しプランへ「今月分だけ」を反映させるための
    集計専用関数。monthly_budget_engine / withdrawal_engineのロジック
    自体には手を加えない。
    """
    if not isinstance(expenses, list):
        raise ValueError("expensesはリスト形式で指定してください。")

    total = 0.0
    for item in expenses:
        if not isinstance(item, dict):
            continue

        month_amounts = _month_amounts(
            amount=item.get("amount", 0.0),
            expected_month=str(item.get("expected_month", "")),
            distribution_months=item.get(
                "distribution_months", DEFAULT_DISTRIBUTION_MONTHS
            ),
        )
        total += month_amounts.get(target_month, 0.0)

    return round(total, 2)


def distribution_end_month(expense: dict) -> str:
    """支出レコードの分散区間の最終月（"YYYY-MM"）を返す。

    distribution_monthsが1（従来通り）の場合はexpected_monthと同じ値を返す。
    表示用の補助関数で、計算ロジックには影響しない。
    """
    expected_month = str(expense.get("expected_month", ""))
    distribution_months = int(
        expense.get("distribution_months", DEFAULT_DISTRIBUTION_MONTHS) or 1
    )
    return _add_months(expected_month, max(distribution_months - 1, 0))
