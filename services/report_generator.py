from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any
import re


UNIT_MAP = {
    "current_age": "歳",
    "end_age": "歳",
    "current_assets": "万円",
    "cash_assets": "万円",
    "annual_spending": "万円/年",
    "annual_side_income": "万円/年",
    "expected_return": "%",
    "inflation": "%",
    "safety_margin": "%",
    "min_cash_months": "か月",
    "nisa_assets": "万円",
    "nisa_contributed": "万円",
    "nisa_growth_contributed": "万円",
    "nisa_annual_contributed": "万円",
    "taxable_assets": "万円",
    "ideco_assets": "万円",
    "ideco_monthly_contribution": "万円/月",
    "ideco_annual_limit": "万円/年",
    "annual_pension": "万円/年",
    "pension_start_age": "歳",
}

LABEL_MAP = {
    "current_age": "現在年齢",
    "end_age": "シミュレーション終了年齢",
    "current_assets": "総金融資産",
    "cash_assets": "現金・預金",
    "annual_spending": "年間生活費",
    "annual_side_income": "年間副収入",
    "expected_return": "想定運用利回り",
    "inflation": "想定インフレ率",
    "safety_margin": "安全余裕率",
    "min_cash_months": "最低現金バッファ",
    "market_condition": "市場環境",
    "nisa_assets": "NISA現在残高",
    "nisa_contributed": "NISA累計投資額・簿価",
    "nisa_growth_contributed": "成長投資枠累計投資額",
    "nisa_annual_contributed": "今年のNISA投資額",
    "taxable_assets": "課税口座残高",
    "ideco_assets": "iDeCo現在残高",
    "ideco_monthly_contribution": "iDeCo月額掛金",
    "ideco_annual_limit": "iDeCo年間上限",
    "annual_pension": "年金見込額",
    "pension_start_age": "年金受給開始年齢",
}


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "はい" if value else "いいえ"
    if isinstance(value, (int, float)):
        return f"{value:,.1f}".rstrip("0").rstrip(".")
    return str(value)


def _input_rows(inputs: dict[str, Any]) -> str:
    rows: list[str] = []
    for key, value in inputs.items():
        label = LABEL_MAP.get(key, key)
        unit = UNIT_MAP.get(key, "")
        display = f"{_format_value(value)}{unit}"
        rows.append(
            f"<tr><th>{escape(label)}</th><td>{escape(display)}</td></tr>"
        )
    return "\n".join(rows)


def _scenario_rows(scenarios: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for scenario in scenarios:
        rows.append(
            "<tr>"
            f"<td>{escape(str(scenario.get('name', '---')))}</td>"
            f"<td>{_format_value(scenario.get('final_assets', 0))}万円</td>"
            f"<td>{_format_value(scenario.get('min_assets', 0))}万円</td>"
            f"<td>{escape(str(scenario.get('depleted_at', '---')))}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def _result_cards(results: dict[str, Any]) -> str:
    cards = [
        ("資産寿命判定", results.get("asset_depletion_label", "---")),
        (
            "推奨月間支出",
            f"{_format_value(results.get('recommended_monthly_spending', 0))}万円",
        ),
        (
            "現金生活費",
            f"{_format_value(results.get('cash_months', 0))}か月",
        ),
        ("市場環境", results.get("market_condition", "---")),
        ("今月の行動候補", results.get("recommended_action", "---")),
        (
            "年金開始後の年間不足",
            f"{_format_value(results.get('pension_gap_after_start', 0))}万円",
        ),
    ]

    return "\n".join(
        f'<div class="card"><div class="label">{escape(str(label))}</div>'
        f'<div class="value">{escape(str(value))}</div></div>'
        for label, value in cards
    )


def build_report_html(record: dict[str, Any]) -> str:
    if not isinstance(record, dict):
        raise ValueError("レポートデータはdict形式で指定してください。")

    name = str(record.get("name", "FIREシミュレーション"))
    created_at = str(record.get("created_at", ""))
    inputs = record.get("inputs", {})
    results = dict(record.get("results", {}))
    scenarios = record.get("scenarios", [])

    if not isinstance(inputs, dict):
        raise ValueError("inputsはdict形式で指定してください。")
    if not isinstance(results, dict):
        raise ValueError("resultsはdict形式で指定してください。")
    if not isinstance(scenarios, list):
        raise ValueError("scenariosはlist形式で指定してください。")

    results.setdefault("market_condition", inputs.get("market_condition", "---"))
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    source_timestamp = created_at or "保存日時不明"

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{escape(name)} - FIRE Compass Report</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.6; margin: 0; background: #f5f7fb; color: #1f2937; }}
.container {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 56px; }}
.header {{ background: #ffffff; padding: 28px; border-radius: 16px; margin-bottom: 20px; }}
h1 {{ margin: 0 0 8px; font-size: 30px; }}
.subtle {{ color: #6b7280; font-size: 14px; }}
h2 {{ margin-top: 28px; }}
.grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
.card {{ background: #ffffff; padding: 18px; border-radius: 14px; min-height: 84px; }}
.card .label {{ color: #6b7280; font-size: 13px; margin-bottom: 8px; }}
.card .value {{ font-size: 22px; font-weight: 700; }}
table {{ width: 100%; border-collapse: collapse; background: #ffffff; border-radius: 14px; overflow: hidden; }}
th, td {{ padding: 12px 14px; border-bottom: 1px solid #e5e7eb; text-align: left; }}
th {{ width: 40%; background: #f9fafb; }}
.notice {{ background: #fff7ed; border-left: 5px solid #f59e0b; padding: 16px 18px; border-radius: 10px; }}
.footer {{ margin-top: 32px; color: #6b7280; font-size: 12px; }}
@media (max-width: 720px) {{ .grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="container">
<section class="header">
<h1>🧭 FIRE Compass レポート</h1>
<p><strong>{escape(name)}</strong></p>
<p class="subtle">履歴保存日時: {escape(source_timestamp)} / レポート生成日時: {escape(generated_at)}</p>
</section>

<h2>1. FIRE状態の概要</h2>
<div class="grid">
{_result_cards(results)}
</div>

<h2>2. シミュレーション入力条件</h2>
<table>
{_input_rows(inputs)}
</table>

<h2>3. シナリオ結果</h2>
<table>
<thead><tr><th>シナリオ</th><th>終了時資産</th><th>最低資産</th><th>資産枯渇</th></tr></thead>
<tbody>
{_scenario_rows(scenarios)}
</tbody>
</table>

<h2>4. 行動候補と税制・年金関連</h2>
<table>
<tr><th>今月の行動候補</th><td>{escape(str(results.get('recommended_action', '---')))}</td></tr>
<tr><th>追加投資候補</th><td>{_format_value(results.get('additional_investment', 0))}万円</td></tr>
<tr><th>投資資産からの補充候補</th><td>{_format_value(results.get('investment_withdrawal', 0))}万円</td></tr>
<tr><th>NISA残り総枠</th><td>{_format_value(results.get('nisa_remaining_limit', 0))}万円</td></tr>
<tr><th>NISA成長投資枠残り</th><td>{_format_value(results.get('nisa_growth_remaining_limit', 0))}万円</td></tr>
<tr><th>今年のNISA残り</th><td>{_format_value(results.get('nisa_annual_room', 0))}万円</td></tr>
<tr><th>iDeCo年額拠出</th><td>{_format_value(results.get('ideco_annual_contribution', 0))}万円</td></tr>
<tr><th>年金開始後の年間不足</th><td>{_format_value(results.get('pension_gap_after_start', 0))}万円</td></tr>
</table>

<h2>5. 注意事項</h2>
<div class="notice">
このレポートは入力条件に基づくシミュレーション結果を整理したものです。<br>
将来の市場収益、物価、収入、年金額などを保証するものではありません。<br>
金融商品の売買や特定の投資行動を断定するものではなく、意思決定を支援するための参考情報です。
</div>

<div class="footer">FIRE Compass / このHTMLをブラウザで開き、「印刷」→「PDFとして保存」でPDF化できます。</div>
</div>
</body>
</html>"""


def report_filename(record: dict[str, Any]) -> str:
    name = str(record.get("name", "FIREシミュレーション"))
    safe = re.sub(r"[^0-9A-Za-zぁ-んァ-ヶ一-龠._-]+", "_", name).strip("._")
    safe = safe or "FIREシミュレーション"
    return f"{safe}_report.html"


def write_report_html(record: dict[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_report_html(record), encoding="utf-8")
    return output
