from dataclasses import dataclass, field
from typing import List

# このモジュールはmonthly_budget_engineが算出した結果（reasonsタグと
# binding_safe_factor_reason）を、日本語の説明文に変換するだけの
# 表示層である。金額や係数の計算は一切行わない
# （「AIは説明のみ担当、数値計算はPythonで行う」というプロジェクトの
# ルールに沿っている）。

# reasonsタグ → 詳細説明文。表示順序はこの辞書の定義順ではなく、
# _DISPLAY_ORDERで明示的に制御する。
_REASON_LABELS = {
    "market_crash_active": (
        "市場が暴落局面と判定されているため、安全生活費を通常の60%に"
        "抑えています。"
    ),
    "bear_case_depletes": (
        "資産寿命シミュレーションの悲観ケースで資産が枯渇する見込みのため、"
        "安全生活費を通常の70%に抑えています。"
    ),
    "cash_buffer_below_target": (
        "現金バッファが目標水準を下回っているため、安全生活費を通常の85%に"
        "抑えています。"
    ),
    "cash_buffer_healthy": (
        "現金バッファは目標水準を満たしており、通常通りの安全生活費を"
        "算出しています。"
    ),
    "early_retirement_stage": (
        "早期リタイア期（60歳〜年金受給開始前）にあたるため、安全生活費を"
        "通常の95%に抑える調整を行っています。"
    ),
    "late_stage_conservative": (
        "75歳以降にあたるため、安全生活費を通常の90%に抑える保守的な"
        "調整を行っています。"
    ),
    "sequence_risk_evaluated": (
        "早期リタイア期のシーケンス・オブ・リターンズ・リスク"
        "（相場が悪いタイミングで取り崩しを始めるリスク）を評価しましたが、"
        "他の要因の方が厳しいため、この評価による追加の調整は"
        "反映されていません。"
    ),
    "sequence_risk_applied": (
        "早期リタイア期のシーケンス・オブ・リターンズ・リスクを評価した"
        "結果、通常の早期リタイア期の調整よりもさらに安全生活費を"
        "厳しめに算出しています。"
    ),
    "upside_allowed": (
        "現在は余裕があるため、上限生活費は通常より15%高めに設定しています。"
    ),
    "large_expense_exceeds_cash_surplus": (
        "今月以降に予定されている大型支出が現金の余力を超えるため、"
        "判定を1段階厳しくしています。"
    ),
    "large_expense_within_cash_surplus": (
        "今月以降に予定されている大型支出はありますが、現金の余力の範囲内の"
        "ため判定への影響はありません。"
    ),
}

# 表示順序（安全生活費の判定に関わる主要因 → ステージ調整 → 系列リスク →
# 上限生活費 → 大型支出、の順）。この辞書にないタグは無視する。
_DISPLAY_ORDER = (
    "market_crash_active",
    "bear_case_depletes",
    "cash_buffer_below_target",
    "cash_buffer_healthy",
    "early_retirement_stage",
    "late_stage_conservative",
    "sequence_risk_applied",
    "sequence_risk_evaluated",
    "upside_allowed",
    "large_expense_exceeds_cash_surplus",
    "large_expense_within_cash_surplus",
)

# binding_safe_factor_reason → 一覧の先頭に出す「今、何が一番効いているか」
# の短いラベル。
_BINDING_LABELS = {
    "market_crash_active": "市場の暴落局面",
    "bear_case_depletes": "資産寿命シミュレーションの悲観ケース",
    "cash_buffer_below_target": "現金バッファ不足",
    "early_retirement_stage": "早期リタイア期の調整",
    "late_stage_conservative": "75歳以降の保守的な調整",
    "sequence_risk_applied": "早期リタイア期のシーケンス・オブ・リターンズ・リスク",
}


@dataclass
class BudgetExplanation:
    binding_summary: str
    details: List[str] = field(default_factory=list)


def build_budget_explanation(
    reasons: List[str],
    binding_safe_factor_reason: str,
) -> BudgetExplanation:
    """monthly_budget_engineのreasons・binding_safe_factor_reasonを、
    ユーザー向けの日本語説明に変換する。

    このモジュールはmonthly_budget_engineの計算結果を受け取って文章化
    するだけで、係数や金額の再計算は一切行わない。
    """
    details: List[str] = []
    seen = set()

    for tag in _DISPLAY_ORDER:
        if tag not in reasons or tag in seen:
            continue

        # sequence_risk_appliedが採用されている場合、evaluatedの説明は
        # 重複するため省略する。
        if tag == "sequence_risk_evaluated" and "sequence_risk_applied" in reasons:
            continue

        label = _REASON_LABELS.get(tag)
        if label:
            details.append(label)
            seen.add(tag)

    if binding_safe_factor_reason == "cash_buffer_healthy":
        binding_summary = (
            "現在、安全生活費を追加で厳しくしている要因はありません"
            "（通常通りの算出です）。"
        )
    else:
        binding_label = _BINDING_LABELS.get(
            binding_safe_factor_reason, "通常のルール"
        )
        binding_summary = (
            f"現在、安全生活費に最も影響しているのは"
            f"「{binding_label}」です。"
        )

    return BudgetExplanation(
        binding_summary=binding_summary,
        details=details,
    )
