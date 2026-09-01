from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

# Sprint 30で追加。FIRE後に給与天引きがなくなり自分で納付が必要になる
# 「国民健康保険料」「国民年金保険料」を、前年所得から概算する。
#
# このモジュールはfire_engine / action_engine / tax_optimization /
# crash_strategy等、既存のロック済み金融計算ロジックには一切関与しない、
# 独立した概算モジュールである。算出した月額はmonthly_budget_engine側で
# 既存の安全/推奨/上限生活費から差し引く形で反映される。
#
# 【重要な前提・簡易化】
# 国民健康保険料は自治体ごとに料率・賦課方式（2方式／3方式）・軽減制度が
# 異なり、正確な金額は居住自治体でしか算出できない。本モジュールは
# 「所得割＋均等割」の2方式（東京23区を含む多くの自治体で採用）を用いた
# 全国的な目安のモデルであり、実際の金額とは異なる場合がある。
# 基礎控除は所得に応じた5段階控除ではなく、簡易的に43万円固定として扱う。
# 賦課限度額（上限）は地方税法で全国一律に定められている値を使用する。
# 軽減制度（均等割の7割・5割・2割軽減等）は考慮しない。
#
# 国民年金保険料は全国一律の定額（年度改定）であり、20歳以上60歳未満が
# 対象（60歳以上は原則対象外。任意加入は考慮しない）。

# --- 国民健康保険料（簡易全国モデル、2方式：所得割＋均等割） ---
# 基礎控除（簡易的に固定額を使用。本来は前年合計所得金額に応じた
# 5段階控除だが、ここでは簡易化のため単純な定額控除とする）。
BASIC_DEDUCTION = 43.0  # 万円

# 医療分（基礎賦課額）
MEDICAL_INCOME_RATE = 0.070  # 所得割率の目安
MEDICAL_PER_CAPITA = 2.5  # 均等割（万円/人）の目安
MEDICAL_CAP = 65.0  # 賦課限度額（万円、世帯単位）

# 支援分（後期高齢者支援金分）
SUPPORT_INCOME_RATE = 0.022
SUPPORT_PER_CAPITA = 0.8
SUPPORT_CAP = 24.0

# 介護分（介護納付金分。40歳以上65歳未満のみ対象）
CARE_INCOME_RATE = 0.020
CARE_PER_CAPITA = 1.0
CARE_CAP = 17.0

CARE_PORTION_START_AGE = 40
CARE_PORTION_END_AGE = 65  # この年齢未満が対象（65歳以上は介護保険第1号被保険者として別枠）

# --- 国民年金保険料（全国一律定額、年度改定） ---
# 令和7年度（2025年4月〜2026年3月）月額の目安。年度が変わるたびに
# 見直しが必要（本モジュール内の定数を更新するだけで反映される）。
NATIONAL_PENSION_MONTHLY_FEE = 1.751  # 万円/月（17,510円の目安）

NATIONAL_PENSION_START_AGE = 20
NATIONAL_PENSION_END_AGE = 60  # この年齢未満が対象（60歳以上は原則対象外）


@dataclass
class HealthInsuranceComponent:
    label: str
    income_levy: float  # 所得割（万円、上限適用前）
    per_capita_levy: float  # 均等割（万円、上限適用前）
    subtotal: float  # 上限適用前の合計（万円）
    capped_amount: float  # 実際に賦課される額（上限適用後、万円）
    capped: bool  # 賦課限度額に達しているか


@dataclass
class SocialInsuranceResult:
    prior_year_income: float
    household_size: int
    current_age: int
    taxable_base: float  # 所得割算定基礎額（基礎控除後、万円）
    health_insurance_components: List[HealthInsuranceComponent] = field(
        default_factory=list
    )
    annual_health_insurance: float = 0.0
    monthly_health_insurance: float = 0.0
    national_pension_applicable: bool = False
    annual_national_pension: float = 0.0
    monthly_national_pension: float = 0.0
    annual_total: float = 0.0
    monthly_total: float = 0.0
    notes: List[str] = field(default_factory=list)


def _build_component(
    label: str,
    taxable_base: float,
    income_rate: float,
    per_capita: float,
    household_size: int,
    cap: float,
) -> HealthInsuranceComponent:
    income_levy = round(taxable_base * income_rate, 2)
    per_capita_levy = round(per_capita * household_size, 2)
    subtotal = round(income_levy + per_capita_levy, 2)
    capped_amount = round(min(subtotal, cap), 2)

    return HealthInsuranceComponent(
        label=label,
        income_levy=income_levy,
        per_capita_levy=per_capita_levy,
        subtotal=subtotal,
        capped_amount=capped_amount,
        capped=subtotal > cap,
    )


def calculate_social_insurance(
    prior_year_income: float,
    household_size: int = 1,
    current_age: int = 0,
) -> SocialInsuranceResult:
    """前年所得・世帯人数・現在年齢から、国民健康保険料と国民年金保険料の
    月額目安を算出する（全国的な簡易モデル。詳細はモジュールdocstring参照）。

    prior_year_income: 前年の年間所得目安（万円）。給与所得だけでなく、
        課税口座の譲渡益・配当等、国保の所得割算定に含まれる所得の合計を
        想定している（給与所得控除後の所得ベースを推奨。厳密な所得区分の
        判定は行わない）。
    household_size: 世帯人数（1以上の整数）。均等割の算定に使用する。
    current_age: 現在年齢。介護分（40〜64歳）・国民年金の対象判定に使用する。
    """
    if prior_year_income < 0:
        raise ValueError("前年所得は0以上にしてください。")

    if household_size < 1:
        raise ValueError("世帯人数は1以上にしてください。")

    if current_age < 0:
        raise ValueError("現在年齢は0以上にしてください。")

    taxable_base = max(prior_year_income - BASIC_DEDUCTION, 0.0)

    components = [
        _build_component(
            "医療分", taxable_base, MEDICAL_INCOME_RATE, MEDICAL_PER_CAPITA,
            household_size, MEDICAL_CAP,
        ),
        _build_component(
            "支援分", taxable_base, SUPPORT_INCOME_RATE, SUPPORT_PER_CAPITA,
            household_size, SUPPORT_CAP,
        ),
    ]

    care_applicable = CARE_PORTION_START_AGE <= current_age < CARE_PORTION_END_AGE
    if care_applicable:
        components.append(
            _build_component(
                "介護分", taxable_base, CARE_INCOME_RATE, CARE_PER_CAPITA,
                household_size, CARE_CAP,
            )
        )

    annual_health_insurance = round(
        sum(component.capped_amount for component in components), 2
    )
    monthly_health_insurance = round(annual_health_insurance / 12.0, 2)

    pension_applicable = (
        NATIONAL_PENSION_START_AGE <= current_age < NATIONAL_PENSION_END_AGE
    )
    annual_national_pension = (
        round(NATIONAL_PENSION_MONTHLY_FEE * 12.0, 2) if pension_applicable else 0.0
    )
    monthly_national_pension = (
        round(NATIONAL_PENSION_MONTHLY_FEE, 2) if pension_applicable else 0.0
    )

    annual_total = round(annual_health_insurance + annual_national_pension, 2)
    monthly_total = round(annual_total / 12.0, 2)

    notes = [
        "国民健康保険料は自治体ごとに料率・軽減制度が異なるため、"
        "ここでの金額は全国的な目安（概算）です。正確な金額は居住自治体で"
        "ご確認ください。",
        "基礎控除は簡易的に43万円固定として計算しています"
        "（所得に応じた5段階控除・軽減制度は考慮していません）。",
    ]

    if not care_applicable and current_age > 0:
        if current_age >= CARE_PORTION_END_AGE:
            notes.append(
                "65歳以上のため、介護分は国民健康保険料に含めていません"
                "（介護保険第1号被保険者として別枠で徴収されます）。"
            )

    if not pension_applicable and current_age > 0:
        if current_age >= NATIONAL_PENSION_END_AGE:
            notes.append(
                "60歳以上のため、国民年金保険料は対象外としています"
                "（任意加入は考慮していません）。"
            )
        elif current_age < NATIONAL_PENSION_START_AGE:
            notes.append(
                "20歳未満のため、国民年金保険料は対象外としています。"
            )

    return SocialInsuranceResult(
        prior_year_income=prior_year_income,
        household_size=household_size,
        current_age=current_age,
        taxable_base=taxable_base,
        health_insurance_components=components,
        annual_health_insurance=annual_health_insurance,
        monthly_health_insurance=monthly_health_insurance,
        national_pension_applicable=pension_applicable,
        annual_national_pension=annual_national_pension,
        monthly_national_pension=monthly_national_pension,
        annual_total=annual_total,
        monthly_total=monthly_total,
        notes=notes,
    )
