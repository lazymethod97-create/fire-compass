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
    "bear_market_active": (
        "市場が弱気相場と判定されているため、安全生活費を通常の95%に"
        "抑えています。"
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
    "social_insurance_deducted": (
        "国民健康保険料・国民年金保険料の月額目安を、安全・推奨・上限生活費"
        "から直接差し引いています。"
    ),
    "resident_tax_deducted": (
        "住民税の月額目安を、安全・推奨・上限生活費から直接差し引いて"
        "います。"
    ),
}

# 表示順序（安全生活費の判定に関わる主要因 → ステージ調整 → 系列リスク →
# 上限生活費 → 大型支出、の順）。この辞書にないタグは無視する。
_DISPLAY_ORDER = (
    "market_crash_active",
    "bear_case_depletes",
    "cash_buffer_below_target",
    "cash_buffer_healthy",
    "bear_market_active",
    "early_retirement_stage",
    "late_stage_conservative",
    "sequence_risk_applied",
    "sequence_risk_evaluated",
    "upside_allowed",
    "large_expense_exceeds_cash_surplus",
    "large_expense_within_cash_surplus",
    "social_insurance_deducted",
    "resident_tax_deducted",
)

# Sprint36で追加。reasonsタグが増え続けてもフラットな箇条書きが
# 際限なく伸びないよう、タグを4つのカテゴリにグルーピングして表示する。
# 新しいタグを追加する際は、_REASON_LABELS・_DISPLAY_ORDERに加えて
# ここにカテゴリを1行追加するだけでよい（app.py側の変更は不要）。
_REASON_CATEGORY = {
    "market_crash_active": "living_cost_adjustment",
    "bear_case_depletes": "living_cost_adjustment",
    "cash_buffer_below_target": "living_cost_adjustment",
    "cash_buffer_healthy": "living_cost_adjustment",
    "bear_market_active": "living_cost_adjustment",
    "early_retirement_stage": "living_cost_adjustment",
    "late_stage_conservative": "living_cost_adjustment",
    "sequence_risk_applied": "living_cost_adjustment",
    "sequence_risk_evaluated": "living_cost_adjustment",
    "upside_allowed": "max_spending",
    "large_expense_exceeds_cash_surplus": "large_expense",
    "large_expense_within_cash_surplus": "large_expense",
    "social_insurance_deducted": "fixed_cost_deduction",
    "resident_tax_deducted": "fixed_cost_deduction",
}

_CATEGORY_LABELS = {
    "living_cost_adjustment": "生活費調整の主な要因",
    "max_spending": "上限生活費",
    "large_expense": "今月以降の大型支出",
    "fixed_cost_deduction": "固定費の控除（概算）",
}

# カテゴリの表示順序。この並びにないカテゴリキーは表示されない
# （_REASON_CATEGORYの値は必ずこの中のいずれかにすること）。
_CATEGORY_ORDER = (
    "living_cost_adjustment",
    "max_spending",
    "large_expense",
    "fixed_cost_deduction",
)

# binding_safe_factor_reason → 一覧の先頭に出す「今、何が一番効いているか」
# の短いラベル。
_BINDING_LABELS = {
    "market_crash_active": "市場の暴落局面",
    "bear_case_depletes": "資産寿命シミュレーションの悲観ケース",
    "cash_buffer_below_target": "現金バッファ不足",
    "bear_market_active": "市場の弱気相場局面",
    "early_retirement_stage": "早期リタイア期の調整",
    "late_stage_conservative": "75歳以降の保守的な調整",
    "sequence_risk_applied": "早期リタイア期のシーケンス・オブ・リターンズ・リスク",
}


@dataclass
class BudgetExplanationGroup:
    """カテゴリ1つ分の見出しと、そのカテゴリに属する説明文のリスト。"""

    category_label: str
    details: List[str] = field(default_factory=list)


@dataclass
class BudgetExplanation:
    binding_summary: str
    groups: List[BudgetExplanationGroup] = field(default_factory=list)


def build_budget_explanation(
    reasons: List[str],
    binding_safe_factor_reason: str,
) -> BudgetExplanation:
    """monthly_budget_engineのreasons・binding_safe_factor_reasonを、
    ユーザー向けの日本語説明に変換する。

    このモジュールはmonthly_budget_engineの計算結果を受け取って文章化
    するだけで、係数や金額の再計算は一切行わない。
    該当するタグが1つもないカテゴリはgroupsに含めない。
    """
    details_by_category: dict[str, List[str]] = {}
    seen = set()

    for tag in _DISPLAY_ORDER:
        if tag not in reasons or tag in seen:
            continue

        # sequence_risk_appliedが採用されている場合、evaluatedの説明は
        # 重複するため省略する。
        if tag == "sequence_risk_evaluated" and "sequence_risk_applied" in reasons:
            continue

        label = _REASON_LABELS.get(tag)
        category = _REASON_CATEGORY.get(tag)
        if label and category:
            details_by_category.setdefault(category, []).append(label)
            seen.add(tag)

    groups = [
        BudgetExplanationGroup(
            category_label=_CATEGORY_LABELS[category],
            details=details_by_category[category],
        )
        for category in _CATEGORY_ORDER
        if category in details_by_category
    ]

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
        groups=groups,
    )