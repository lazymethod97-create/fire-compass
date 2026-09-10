from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from services.fire_engine import FireInput

# リターンが物理的にありえない値（1年で資産が100%超のマイナスになる等）を
# 避けるための下限。極端な乱数が出た場合の安全弁であり、通常の
# パラメータ範囲ではほぼ影響しない。
_MIN_ANNUAL_RETURN = -0.99


@dataclass
class MonteCarloResult:
    success_rate_pct: float
    num_trials: int
    volatility_pct: float
    yearly_df: pd.DataFrame  # 列: age, p10, p50, p90


def run_monte_carlo_simulation(
    inputs: FireInput,
    volatility_pct: float,
    num_trials: int = 5000,
    seed: int | None = 42,
) -> MonteCarloResult:
    """想定利回りにランダムな年次変動（ボラティリティ）を与え、
    資産が枯渇せず終了年齢まで持つ確率を試算する。

    fire_engine.run_fire_simulation()と同じ「毎年、資産を運用リターン分
    増減させ、生活費（インフレ調整後）を差し引く。0を下回ったら0のまま
    （そこから回復しない）」という更新ルールをそのまま踏襲し、リターンだけ
    年ごと・試行ごとにランダム化する。fire_engine.py／他の計算エンジンは
    一切変更していない（FireInputを読み取るだけ）。

    Args:
        inputs: fire_engine.FireInputと同じ入力（total_assets・
            annual_spending等をそのまま利用する）。
        volatility_pct: 年次リターンの標準偏差（%）。既定値は呼び出し側
            （app.py）で15%を提案している。
        num_trials: 試行回数。既定5000回。
        seed: 乱数シード。既定42で固定し、同じ入力なら同じ結果を返す
            （再実行のたびに数値がぶれると信頼性を損なうため）。
            Noneを渡すと毎回変わる。

    Returns:
        MonteCarloResult: 成功率（％）と、年齢ごとの資産分布
        （10/50/90パーセンタイル）。
    """
    if inputs.end_age <= inputs.current_age:
        raise ValueError("終了年齢は現在年齢より大きくしてください。")

    if volatility_pct < 0:
        raise ValueError("ボラティリティは0以上にしてください。")

    if num_trials <= 0:
        raise ValueError("試行回数は1以上にしてください。")

    net_annual_spending = max(
        inputs.annual_spending - inputs.annual_side_income, 0.0
    )

    years = inputs.end_age - inputs.current_age + 1
    ages = np.arange(inputs.current_age, inputs.end_age + 1)

    rng = np.random.default_rng(seed)
    mean_return = inputs.expected_return_pct / 100.0
    std_return = volatility_pct / 100.0
    inflation_rate = inputs.inflation_pct / 100.0

    returns = rng.normal(loc=mean_return, scale=std_return, size=(num_trials, years))
    returns = np.clip(returns, _MIN_ANNUAL_RETURN, None)

    assets = np.full(num_trials, inputs.total_assets, dtype=float)
    spending = net_annual_spending
    trajectory = np.empty((num_trials, years), dtype=float)

    for year_index in range(years):
        trajectory[:, year_index] = np.maximum(assets, 0.0)
        assets = assets * (1.0 + returns[:, year_index]) - spending
        assets = np.maximum(assets, 0.0)
        spending *= 1.0 + inflation_rate

    success_rate_pct = round(float(np.mean(assets > 0.0)) * 100.0, 1)

    yearly_df = pd.DataFrame(
        {
            "age": ages,
            "p10": np.percentile(trajectory, 10, axis=0),
            "p50": np.percentile(trajectory, 50, axis=0),
            "p90": np.percentile(trajectory, 90, axis=0),
        }
    )

    return MonteCarloResult(
        success_rate_pct=success_rate_pct,
        num_trials=num_trials,
        volatility_pct=volatility_pct,
        yearly_df=yearly_df,
    )