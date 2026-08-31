import os
from typing import Any

from services.app_logger import log_event
from services.security import safe_error_message

DEFAULT_MODEL = "gemini-2.5-flash"


def _scenario_text(scenario: Any) -> str:
    return (
        f"{scenario.name}: "
        f"終了時資産={scenario.final_assets:,.0f}万円, "
        f"最低資産={scenario.min_assets:,.0f}万円, "
        f"資産枯渇={scenario.depleted_at}"
    )


def _build_fallback_advice(
    fire_result: Any,
    market_condition: str,
    strategy: Any,
    recommended_action: str,
    additional_investment: float,
    investment_withdrawal: float,
) -> str:
    lines = [
        "### AI FIREアドバイス（ルールベース）",
        "",
        f"**市場環境：{market_condition}**",
        "",
        "#### 現状",
        f"- 純年間支出：{fire_result.net_annual_spending:,.0f}万円",
        f"- 推奨月間支出：{strategy.recommended_monthly_spending:,.1f}万円",
        f"- 現金：{fire_result.cash_months:.1f}か月分",
        f"- 資産寿命判定：{fire_result.asset_depletion_label}",
        "",
        "#### 今月の判断",
        f"- 推奨行動：{recommended_action}",
        f"- 追加投資候補：{additional_investment:,.1f}万円",
        f"- 投資資産からの補充候補：{investment_withdrawal:,.1f}万円",
        f"- 目標現金：{strategy.target_cash_months:.0f}か月分",
        "",
        "#### リスク",
        f"- {fire_result.advice}",
        "",
        "#### 防御ルール",
        f"- {strategy.reason}",
    ]

    return "\n".join(lines)


def _build_prompt(
    fire_result: Any,
    market_condition: str,
    strategy: Any,
    recommended_action: str,
    additional_investment: float,
    investment_withdrawal: float,
) -> str:
    scenarios = "\n".join(
        _scenario_text(scenario)
        for scenario in fire_result.scenario_summaries
    )

    return f"""
あなたはFIRE（早期リタイア）計画を支援するアドバイザーです。

以下のシミュレーション結果だけを根拠に、日本語で分かりやすく説明してください。

重要なルール:
- 投資商品の売買を断定しない
- 「必ず」「絶対」などの断定表現を避ける
- 入力された数値を勝手に変更しない
- 不明な情報を推測しない
- 最終判断はユーザー自身が行う前提にする
- 初心者にも分かる表現にする
- 300〜500文字程度にまとめる

出力形式:
### 現状
現在のFIRE状態を説明。

### リスク
資産寿命、現金バッファ、市場環境から見た注意点。

### 今月やること
具体的な行動候補を3つ以内で説明。

【FIREシミュレーション】
純年間支出: {fire_result.net_annual_spending:,.1f}万円
推奨月間支出: {fire_result.recommended_monthly_spending:,.1f}万円
現金生活費: {fire_result.cash_months:.1f}か月
資産寿命判定: {fire_result.asset_depletion_label}

【市場環境】
{market_condition}

【市場環境ルール】
目標現金: {strategy.target_cash_months:.1f}か月
追加投資率: {strategy.additional_investment_ratio * 100:.0f}%
生活費削減率: {strategy.spending_reduction_pct:.0f}%
推奨月間生活費: {strategy.recommended_monthly_spending:,.1f}万円

【今月の推奨行動】
{recommended_action}
追加投資候補: {additional_investment:,.1f}万円
投資資産からの補充候補: {investment_withdrawal:,.1f}万円

【資産シミュレーション】
{scenarios}

【既存のルールベース助言】
{fire_result.advice}
""".strip()


def generate_ai_advice(
    fire_result: Any,
    market_condition: str,
    strategy: Any,
    recommended_action: str,
    additional_investment: float,
    investment_withdrawal: float,
) -> str:
    """
    Gemini APIを利用してFIREアドバイスを生成する。

    APIキー未設定・SDKエラー・APIエラー時は、
    安全なルールベースのアドバイスへフォールバックする。
    """

    fallback = _build_fallback_advice(
        fire_result=fire_result,
        market_condition=market_condition,
        strategy=strategy,
        recommended_action=recommended_action,
        additional_investment=additional_investment,
        investment_withdrawal=investment_withdrawal,
    )

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        log_event(
            "ai_advice_fallback",
            "GEMINI_API_KEY未設定のため、ルールベースのアドバイスへフォールバックしました。",
            level="INFO",
        )
        return fallback

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
            contents=_build_prompt(
                fire_result=fire_result,
                market_condition=market_condition,
                strategy=strategy,
                recommended_action=recommended_action,
                additional_investment=additional_investment,
                investment_withdrawal=investment_withdrawal,
            ),
        )

        text = getattr(response, "text", None)

        if text and text.strip():
            return text.strip()

        log_event(
            "ai_advice_fallback",
            "Gemini APIから空の応答を受け取ったため、ルールベースへフォールバックしました。",
            level="WARNING",
        )
        return fallback

    except Exception as error:
        log_event(
            "ai_advice_fallback",
            "Gemini API呼び出しでエラーが発生したため、ルールベースへフォールバックしました。"
            f" 詳細: {safe_error_message(error)}",
            level="ERROR",
        )
        return fallback


# --- Sprint 29で追加。保有ファンドのバランス（配分比率・集中度）の
# 総評を生成する。数値の算出はservices.portfolio_balance_engineが担当し、
# ここでは算出済みの結果（PortfolioBalanceResult）を受け取って文章化する
# だけで、配分比率・集中度そのものの再計算は一切行わない。
# generate_ai_advice()と同じ設計方針（Gemini未設定・エラー時はルール
# ベースへフォールバック、断定的な投資助言を避ける）に揃えている。


def _build_portfolio_fallback_commentary(balance: Any) -> str:
    lines = [
        "### 保有ファンドのバランス（ルールベース）",
        "",
        f"評価額合計：{balance.total_valuation:,.1f}万円",
        "",
        "#### カテゴリ別配分",
    ]
    for slice_ in balance.by_category:
        lines.append(
            f"- {slice_.label}：{slice_.weight_pct:.1f}%"
            f"（{slice_.valuation_amount:,.1f}万円）"
        )

    lines.append("")
    lines.append("#### 口座種別の配分")
    for slice_ in balance.by_account_type:
        lines.append(
            f"- {slice_.label}：{slice_.weight_pct:.1f}%"
            f"（{slice_.valuation_amount:,.1f}万円）"
        )

    if balance.concentration_warnings:
        lines.append("")
        lines.append("#### 集中度に関する事実")
        for warning in balance.concentration_warnings:
            lines.append(f"- {warning}")

    if balance.uncategorized_fund_names:
        lines.append("")
        lines.append("#### 分類できなかったファンド")
        lines.append("- " + "、".join(balance.uncategorized_fund_names))

    lines.append("")
    lines.append(
        "※ここでは配分の事実を示すのみで、売買の推奨は行いません。"
        "最終判断はご自身で行ってください。"
    )

    return "\n".join(lines)


def _build_portfolio_prompt(balance: Any) -> str:
    category_lines = "\n".join(
        f"{s.label}: {s.weight_pct:.1f}%（{s.valuation_amount:,.1f}万円）"
        for s in balance.by_category
    ) or "データなし"

    account_lines = "\n".join(
        f"{s.label}: {s.weight_pct:.1f}%（{s.valuation_amount:,.1f}万円）"
        for s in balance.by_account_type
    ) or "データなし"

    fund_lines = "\n".join(
        f"{s.label}: {s.weight_pct:.1f}%（{s.valuation_amount:,.1f}万円）"
        for s in balance.by_fund
    ) or "データなし"

    warnings_text = "\n".join(balance.concentration_warnings) or "特になし"
    uncategorized_text = "、".join(balance.uncategorized_fund_names) or "なし"

    return f"""
あなたはFIRE（早期リタイア）計画を支援するアドバイザーです。

以下は、ユーザーが保有する投資信託の配分データです。この事実だけを根拠に、
日本語で分かりやすく解説してください。

重要なルール:
- 投資商品の売買を断定しない（「売るべき」「買い増すべき」等は書かない）
- 「必ず」「絶対」などの断定表現を避ける
- 入力された数値を勝手に変更しない
- 与えられていない情報（個別銘柄の将来の値動き等）を推測しない
- 最終判断はユーザー自身が行う前提にする
- 初心者にも分かる表現にする
- 300〜500文字程度にまとめる

出力形式:
### 配分の特徴
カテゴリ・口座種別の配分から読み取れる特徴を説明。

### 気になる点
集中度など、数値から見て留意すべき点があれば説明（なければその旨）。

### 補足
分類できなかったファンドがあれば触れる。

【評価額合計】
{balance.total_valuation:,.1f}万円

【カテゴリ別配分】
{category_lines}

【口座種別の配分】
{account_lines}

【ファンド別配分】
{fund_lines}

【集中度に関する事実】
{warnings_text}

【分類できなかったファンド】
{uncategorized_text}
""".strip()


def generate_portfolio_commentary(balance: Any) -> str:
    """
    Gemini APIを利用して保有ファンドのバランスに関する総評を生成する。

    APIキー未設定・SDKエラー・APIエラー時は、安全なルールベースの解説へ
    フォールバックする（generate_ai_advice()と同じ方針）。
    保有ファンドが1件もない場合は、Gemini呼び出し自体を行わずその旨を返す。
    """
    if not balance.by_fund:
        return "保有ファンドが取り込まれていないため、バランスを評価できません。"

    fallback = _build_portfolio_fallback_commentary(balance)

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        log_event(
            "portfolio_commentary_fallback",
            "GEMINI_API_KEY未設定のため、ルールベースの解説へフォールバックしました。",
            level="INFO",
        )
        return fallback

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
            contents=_build_portfolio_prompt(balance),
        )

        text = getattr(response, "text", None)

        if text and text.strip():
            return text.strip()

        log_event(
            "portfolio_commentary_fallback",
            "Gemini APIから空の応答を受け取ったため、ルールベースへフォールバックしました。",
            level="WARNING",
        )
        return fallback

    except Exception as error:
        log_event(
            "portfolio_commentary_fallback",
            "Gemini API呼び出しでエラーが発生したため、ルールベースへフォールバックしました。"
            f" 詳細: {safe_error_message(error)}",
            level="ERROR",
        )
        return fallback