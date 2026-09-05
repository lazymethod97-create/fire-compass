from __future__ import annotations

from dataclasses import dataclass

# Sprint 32で追加。住民税（個人住民税）を前年所得から概算する。
#
# 国民健康保険料と同様、FIRE後は特別徴収（給与天引き）がなくなり、
# 普通徴収（自分での納付）に切り替わる。住民税も国保と同じく前年の
# 所得を基準に課税されるため、FIRE直後の1〜2年は在職中の高い所得を
# 基準に算定される「ラグ」が生じる。
#
# social_insurance_engine.py（国保・国民年金）とはあえてモジュールを
# 分けている。住民税の均等割は世帯人数に関係なく個人単位の定額であり、
# 国保のような世帯人数入力・賦課限度額（上限）の仕組みも存在しないため、
# 計算の性質が異なる。fire_engine / action_engine / tax_optimization /
# crash_strategy等、既存のロック済み金融計算ロジックには一切関与しない。
#
# 【重要な前提・簡易化】
# 住民税の所得割率（合計10%：市町村民税6%＋道府県民税4%）はほぼ全国一律
# だが、均等割・基礎控除は自治体の条例や軽減制度によって多少異なる場合が
# ある。本モジュールは全国的な標準額を用いた簡易モデルであり、実際の
# 金額とは異なる場合がある。ふるさと納税による税額控除、住宅ローン控除、
# 各種所得控除（社会保険料控除・扶養控除等）は考慮しない。低所得者向けの
# 均等割非課税制度も考慮しない。

# 基礎控除（social_insurance_engine.pyと同じ簡易的な固定額を使用）。
BASIC_DEDUCTION = 43.0  # 万円

# 所得割率（市町村民税6%＋道府県民税4%の合計、全国ほぼ共通）。
INCOME_LEVY_RATE = 0.10

# 均等割（市町村民税3,000円＋道府県民税1,000円＋森林環境税1,000円＝
# 5,000円/年、令和6年度以降の全国標準額）。国保と異なり個人単位の定額で、
# 世帯人数によって変動しない。
PER_CAPITA_LEVY = 0.5  # 万円/年


@dataclass
class ResidentTaxResult:
    prior_year_income: float
    taxable_base: float  # 所得割算定基礎額（基礎控除後、万円）
    income_levy: float  # 所得割（万円/年）
    per_capita_levy: float  # 均等割（万円/年）
    annual_total: float
    monthly_total: float
    notes: list[str]


def calculate_resident_tax(prior_year_income: float) -> ResidentTaxResult:
    """前年所得から、住民税（個人住民税）の月額目安を算出する
    （全国的な簡易モデル。詳細はモジュールdocstring参照）。

    prior_year_income: 前年の年間所得目安（万円）。
        services.social_insurance_engine.calculate_social_insurance()に
        渡すものと同じ値を想定している（給与所得だけでなく、課税口座の
        譲渡益・配当等を含む所得の合計）。
    """
    if prior_year_income < 0:
        raise ValueError("前年所得は0以上にしてください。")

    taxable_base = max(prior_year_income - BASIC_DEDUCTION, 0.0)

    income_levy = round(taxable_base * INCOME_LEVY_RATE, 2)
    per_capita_levy = round(PER_CAPITA_LEVY, 2)

    annual_total = round(income_levy + per_capita_levy, 2)
    monthly_total = round(annual_total / 12.0, 2)

    notes = [
        "住民税は自治体の条例や軽減制度により実際の金額と異なる場合が"
        "あります。ここでの金額は全国的な標準額による目安（概算）です。",
        "基礎控除は簡易的に43万円固定として計算しています"
        "（ふるさと納税・住宅ローン控除等の税額控除、社会保険料控除・"
        "扶養控除等の所得控除、均等割の非課税制度は考慮していません）。",
    ]

    return ResidentTaxResult(
        prior_year_income=prior_year_income,
        taxable_base=taxable_base,
        income_levy=income_levy,
        per_capita_levy=per_capita_levy,
        annual_total=annual_total,
        monthly_total=monthly_total,
        notes=notes,
    )
