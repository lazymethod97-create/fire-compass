from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime, timezone
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


def format_comparison_value(value: Any, diff: float | None, unit: str) -> str:
    """比較テーブルの1セルを表示用文字列に整形する。

    pages/9_📊_シミュレーション比較.pyとCSVエクスポートの両方から
    同じ整形ロジックを利用するための共通関数（表示の整形のみで、
    金融計算は一切行わない）。
    """
    if value is None:
        display = "---"
    elif _is_numeric(value):
        display = f"{value:,.1f}{unit}"
    else:
        display = f"{value}{unit}"

    if diff is not None and diff != 0:
        sign = "+" if diff > 0 else ""
        display += f"（{sign}{diff:,.1f}）"

    return display


def export_comparison_to_csv(comparison: ComparisonResult) -> str:
    """比較結果（ComparisonResult）をCSV文字列へ変換する。

    Sprint 11のapp_logger.export_events_to_csvと同じ方針で、
    Excel（Windows）で文字化けしないようUTF-8 BOM付き・CRLF区切りで出力する。
    金融計算やAIアドバイスのロジックには一切関与しない、表示専用の整形関数。
    """
    if not isinstance(comparison, ComparisonResult):
        raise ValueError("comparisonはComparisonResult形式で指定してください。")

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")

    writer.writerow(["比較対象"] + comparison.names)
    writer.writerow(["実行日時"] + comparison.created_ats)

    for row in comparison.rows:
        label = f"{row.label}" + (f"（{row.unit}）" if row.unit else "")
        cells = [
            format_comparison_value(value, diff, row.unit)
            for value, diff in zip(row.values, row.diffs)
        ]
        writer.writerow([label] + cells)

    return "\ufeff" + buffer.getvalue()


def comparison_export_filename() -> str:
    """比較結果CSVダウンロード用のファイル名を生成する。"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"fire_compass_comparison_{timestamp}.csv"
