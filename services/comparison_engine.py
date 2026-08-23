from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MIN_RECORDS = 2
MAX_RECORDS = 4

METRIC_DEFS: list[tuple[str, str, str]] = [
    ("asset_depletion_label", "資産寿命判定", ""),
    ("net_annual_spending", "純年間支出", "万円"),
    ("recommended_monthly_spending", "推奨月間支出", "万円"),
    ("cash_months", "現金生活費", "か月"),
    ("target_cash", "目標現金", "万円"),
    ("additional_investment", "追加投資額", "万円"),
    ("investment_withdrawal", "取り崩し額", "万円"),
    ("recommended_action", "今月の推奨行動", ""),
    ("pension_gap_after_start", "年金開始後の年間不足", "万円"),
    ("nisa_remaining_limit", "NISA残り総枠", "万円"),
    ("nisa_growth_remaining_limit", "NISA成長枠残り", "万円"),
    ("nisa_annual_room", "今年のNISA残り", "万円"),
    ("ideco_annual_contribution", "iDeCo年額拠出", "万円"),
]


@dataclass
class ComparisonRow:
    key: str
    label: str
    unit: str
    values: list[Any]
    diffs: list[float | None]


@dataclass
class ComparisonResult:
    names: list[str]
    created_ats: list[str]
    rows: list[ComparisonRow]


def _is_numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def build_comparison(records: list[dict]) -> ComparisonResult:
    """保存済みシミュレーション履歴（2〜4件）から比較テーブルを組み立てる。

    金融計算は一切行わず、Sprint 6で保存済みのresultsフィールドを
    並べて表示するための整形のみを担当する。
    """
    if not isinstance(records, list):
        raise ValueError("比較対象はリスト形式で指定してください。")

    if len(records) < MIN_RECORDS:
        raise ValueError(f"比較には{MIN_RECORDS}件以上の履歴を選択してください。")

    if len(records) > MAX_RECORDS:
        raise ValueError(f"比較できる履歴は最大{MAX_RECORDS}件までです。")

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("比較対象の履歴データはdict形式で指定してください。")

    names = [str(record.get("name", "名称未設定")) for record in records]
    created_ats = [str(record.get("created_at", "日時不明")) for record in records]

    rows: list[ComparisonRow] = []

    for key, label, unit in METRIC_DEFS:
        values = [record.get("results", {}).get(key) for record in records]
        baseline = values[0]

        diffs: list[float | None] = []
        for value in values:
            if _is_numeric(value) and _is_numeric(baseline):
                diffs.append(round(value - baseline, 2))
            else:
                diffs.append(None)

        rows.append(
            ComparisonRow(
                key=key,
                label=label,
                unit=unit,
                values=values,
                diffs=diffs,
            )
        )

    return ComparisonResult(
        names=names,
        created_ats=created_ats,
        rows=rows,
    )
