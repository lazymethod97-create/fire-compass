from dataclasses import dataclass
from typing import List

import pandas as pd


@dataclass
class FireInput:
    current_age: int
    end_age: int
    total_assets: float
    cash_assets: float
    annual_spending: float
    annual_side_income: float
    expected_return_pct: float
    inflation_pct: float
    safety_margin_pct: float


@dataclass
class ScenarioSummary:
    name: str
    final_assets: float
    min_assets: float
    depleted_at: str


@dataclass
class FireResult:
    net_annual_spending: float
    recommended_monthly_spending: float
    cash_months: float
    asset_depletion_label: str
    advice: str
    yearly_df: pd.DataFrame
    scenario_summaries: List[ScenarioSummary]


def _simulate(
    start_assets: float,
    start_age: int,
    end_age: int,
    annual_spending: float,
    annual_income: float,
    return_rate: float,
    inflation_rate: float,
):
    rows = []
    assets = start_assets
    spending = annual_spending

    for age in range(start_age, end_age + 1):
        rows.append({"age": age, "assets": max(assets, 0.0)})

        annual_net_outflow = max(spending - annual_income, 0.0)
        assets = assets * (1.0 + return_rate) - annual_net_outflow
        spending *= 1.0 + inflation_rate

        if assets < 0:
            assets = 0.0

    return pd.DataFrame(rows)


def run_fire_simulation(inputs: FireInput) -> FireResult:
    if inputs.end_age <= inputs.current_age:
        raise ValueError("終了年齢は現在年齢より大きくしてください。")

    if inputs.cash_assets > inputs.total_assets:
        raise ValueError("現金・預金は総金融資産以下にしてください。")

    net_annual_spending = max(
        inputs.annual_spending - inputs.annual_side_income, 0.0
    )

    base_monthly = net_annual_spending / 12.0
    recommended_monthly = round(base_monthly * (1.0 - inputs.safety_margin_pct / 100.0), 2)

    cash_months = (
        inputs.cash_assets / net_annual_spending * 12.0
        if net_annual_spending > 0
        else 999.0
    )

    scenarios = {
        "standard": inputs.expected_return_pct / 100.0,
        "bear": max((inputs.expected_return_pct - 2.0) / 100.0, -1.0),
        "bull": (inputs.expected_return_pct + 2.0) / 100.0,
    }

    scenario_frames = {}
    summaries = []

    scenario_names = {
        "standard": "標準ケース",
        "bear": "悲観ケース",
        "bull": "楽観ケース",
    }

    for key, return_rate in scenarios.items():
        df = _simulate(
            start_assets=inputs.total_assets,
            start_age=inputs.current_age,
            end_age=inputs.end_age,
            annual_spending=inputs.annual_spending,
            annual_income=inputs.annual_side_income,
            return_rate=return_rate,
            inflation_rate=inputs.inflation_pct / 100.0,
        )
        scenario_frames[key] = df

        min_assets = float(df["assets"].min())
        final_assets = float(df.iloc[-1]["assets"])
        depletion_rows = df[df["assets"] <= 0]

        if depletion_rows.empty:
            depleted_at = "期間内に枯渇せず"
        else:
            depleted_at = f'{int(depletion_rows.iloc[0]["age"])}歳頃'

        summaries.append(
            ScenarioSummary(
                name=scenario_names[key],
                final_assets=final_assets,
                min_assets=min_assets,
                depleted_at=depleted_at,
            )
        )

    yearly_df = pd.DataFrame(
        {
            "age": scenario_frames["standard"]["age"],
            "standard": scenario_frames["standard"]["assets"],
            "bear": scenario_frames["bear"]["assets"],
            "bull": scenario_frames["bull"]["assets"],
        }
    )

    standard_end = summaries[0].final_assets
    bear_end = summaries[1].final_assets

    if bear_end <= 0:
        advice = (
            "悲観ケースではシミュレーション期間中に資産が枯渇する可能性があります。"
            "生活費を下げる、副収入を確保する、またはFIRE開始時期を見直す必要があります。"
        )
        asset_depletion_label = "要注意"
    elif cash_months < 12:
        advice = (
            "現金が年間生活費1年分を下回っています。"
            "投資資産を売却する場面が市場下落と重なる可能性があるため、"
            "現金比率を高めることを検討してください。"
        )
        asset_depletion_label = "十分な余裕"
    elif standard_end >= inputs.total_assets:
        advice = (
            "標準ケースでは資産を維持または増加させながら生活できる計算です。"
            "ただし実際の市場リターンは一定ではないため、定期的な見直しが必要です。"
        )
        asset_depletion_label = "余裕あり"
    else:
        advice = (
            "標準ケースでは資産を取り崩しながら生活する計画です。"
            "毎年1回以上、資産残高・生活費・市場環境を確認する設計を推奨します。"
        )
        asset_depletion_label = "計画的な取り崩し"

    return FireResult(
        net_annual_spending=net_annual_spending,
        recommended_monthly_spending=recommended_monthly,
        cash_months=cash_months,
        asset_depletion_label=asset_depletion_label,
        advice=advice,
        yearly_df=yearly_df,
        scenario_summaries=summaries,
    )
