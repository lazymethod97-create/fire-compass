from dataclasses import dataclass

NISA_TOTAL_LIMIT = 1_800.0
NISA_GROWTH_LIMIT = 1_200.0
NISA_ANNUAL_LIMIT = 360.0
IDECO_DEFAULT_ANNUAL_LIMIT = 74.4


@dataclass
class TaxOptimizationInput:
    nisa_assets: float
    nisa_contributed: float
    nisa_growth_contributed: float
    nisa_annual_contributed: float
    taxable_assets: float
    ideco_assets: float
    ideco_monthly_contribution: float
    ideco_annual_limit: float
    current_age: int
    pension_start_age: int
    annual_pension: float
    annual_spending: float
    end_age: int


@dataclass
class TaxOptimizationResult:
    nisa_remaining_limit: float
    nisa_growth_remaining_limit: float
    nisa_annual_room: float
    ideco_annual_contribution: float
    ideco_access_age: int
    pension_start_age: int
    pension_annual_income: float
    pension_monthly_income: float
    pension_gap_before_start: float
    pension_gap_after_start: float
    recommendation: str


def calculate_nisa_room(
    contributed: float,
    growth_contributed: float,
    annual_contributed: float = 0.0,
) -> tuple[float, float, float]:
    if contributed < 0:
        raise ValueError("NISA投資額は0以上にしてください。")
    if growth_contributed < 0:
        raise ValueError("NISA成長投資枠の投資額は0以上にしてください。")
    if growth_contributed > contributed:
        raise ValueError("成長投資枠の投資額はNISA総投資額以下にしてください。")
    if annual_contributed < 0:
        raise ValueError("年間NISA投資額は0以上にしてください。")

    total_room = max(NISA_TOTAL_LIMIT - contributed, 0.0)
    growth_room = max(NISA_GROWTH_LIMIT - growth_contributed, 0.0)
    annual_room = max(NISA_ANNUAL_LIMIT - annual_contributed, 0.0)
    return total_room, growth_room, annual_room


def calculate_ideco_contribution(
    monthly_contribution: float,
    annual_limit: float = IDECO_DEFAULT_ANNUAL_LIMIT,
) -> float:
    if monthly_contribution < 0:
        raise ValueError("iDeCo月額掛金は0以上にしてください。")
    if annual_limit < 0:
        raise ValueError("iDeCo年間上限は0以上にしてください。")
    return min(monthly_contribution * 12.0, annual_limit)


def calculate_pension_gap(
    annual_spending: float,
    annual_pension: float,
) -> float:
    if annual_spending < 0 or annual_pension < 0:
        raise ValueError("生活費と年金額は0以上にしてください。")
    return max(annual_spending - annual_pension, 0.0)


def run_tax_optimization(inputs: TaxOptimizationInput) -> TaxOptimizationResult:
    if inputs.end_age <= inputs.current_age:
        raise ValueError("終了年齢は現在年齢より大きくしてください。")

    if inputs.pension_start_age < 65 or inputs.pension_start_age > 75:
        raise ValueError("年金受給開始年齢は65歳から75歳の範囲で指定してください。")

    numeric_values = (
        inputs.nisa_assets,
        inputs.taxable_assets,
        inputs.ideco_assets,
        inputs.nisa_contributed,
        inputs.nisa_growth_contributed,
        inputs.nisa_annual_contributed,
        inputs.ideco_monthly_contribution,
        inputs.ideco_annual_limit,
        inputs.annual_pension,
        inputs.annual_spending,
    )
    if any(value < 0 for value in numeric_values):
        raise ValueError("金額は0以上にしてください。")

    nisa_total_room, nisa_growth_room, nisa_annual_room = calculate_nisa_room(
        inputs.nisa_contributed,
        inputs.nisa_growth_contributed,
        inputs.nisa_annual_contributed,
    )

    ideco_annual = calculate_ideco_contribution(
        inputs.ideco_monthly_contribution,
        inputs.ideco_annual_limit,
    )

    pension_gap_after_start = calculate_pension_gap(
        inputs.annual_spending,
        inputs.annual_pension,
    )

    if nisa_annual_room > 0:
        recommendation = (
            f"NISAの年間投資余地は{nisa_annual_room:,.0f}万円です。"
            "まずNISAの年間投資枠と生涯の非課税保有限度額の残りを確認します。"
        )
    elif nisa_total_room > 0:
        recommendation = (
            "今年のNISA年間投資枠は使い切っています。"
            "翌年以降のNISA枠とiDeCoの拠出余地を確認します。"
        )
    else:
        recommendation = (
            "NISAの非課税保有限度額は上限に達しています。"
            "iDeCoの拠出余地と年金受給開始後の生活費不足額を確認します。"
        )

    return TaxOptimizationResult(
        nisa_remaining_limit=nisa_total_room,
        nisa_growth_remaining_limit=nisa_growth_room,
        nisa_annual_room=nisa_annual_room,
        ideco_annual_contribution=ideco_annual,
        ideco_access_age=60,
        pension_start_age=inputs.pension_start_age,
        pension_annual_income=inputs.annual_pension,
        pension_monthly_income=inputs.annual_pension / 12.0,
        pension_gap_before_start=inputs.annual_spending,
        pension_gap_after_start=pension_gap_after_start,
        recommendation=recommendation,
    )
