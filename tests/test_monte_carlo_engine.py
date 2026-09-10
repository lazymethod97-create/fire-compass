from __future__ import annotations

import pytest

from services.fire_engine import FireInput
from services.monte_carlo_engine import run_monte_carlo_simulation


def _base_inputs(**overrides) -> FireInput:
    defaults = dict(
        current_age=50,
        end_age=80,
        total_assets=5000.0,
        cash_assets=500.0,
        annual_spending=300.0,
        annual_side_income=0.0,
        expected_return_pct=4.0,
        inflation_pct=1.0,
        safety_margin_pct=10.0,
    )
    defaults.update(overrides)
    return FireInput(**defaults)


def test_raises_when_end_age_not_after_current_age():
    with pytest.raises(ValueError):
        run_monte_carlo_simulation(
            _base_inputs(current_age=60, end_age=60), volatility_pct=15.0
        )


def test_raises_on_negative_volatility():
    with pytest.raises(ValueError):
        run_monte_carlo_simulation(_base_inputs(), volatility_pct=-1.0)


def test_raises_on_non_positive_num_trials():
    with pytest.raises(ValueError):
        run_monte_carlo_simulation(_base_inputs(), volatility_pct=15.0, num_trials=0)


def test_zero_volatility_is_fully_deterministic():
    # ボラティリティ0なら全試行が同じ結果になるため、成功率は0か100のどちらか。
    result = run_monte_carlo_simulation(
        _base_inputs(), volatility_pct=0.0, num_trials=200, seed=1
    )
    assert result.success_rate_pct in (0.0, 100.0)

    # 全試行が同一なので、パーセンタイル同士も一致するはず。
    for _, row in result.yearly_df.iterrows():
        assert row["p10"] == pytest.approx(row["p50"])
        assert row["p50"] == pytest.approx(row["p90"])


def test_success_rate_within_valid_range():
    result = run_monte_carlo_simulation(
        _base_inputs(), volatility_pct=15.0, num_trials=1000, seed=7
    )
    assert 0.0 <= result.success_rate_pct <= 100.0


def test_yearly_df_covers_full_age_range():
    result = run_monte_carlo_simulation(
        _base_inputs(current_age=50, end_age=55), volatility_pct=15.0, num_trials=100
    )
    assert list(result.yearly_df["age"]) == [50, 51, 52, 53, 54, 55]


def test_same_seed_is_reproducible():
    result_a = run_monte_carlo_simulation(
        _base_inputs(), volatility_pct=15.0, num_trials=500, seed=99
    )
    result_b = run_monte_carlo_simulation(
        _base_inputs(), volatility_pct=15.0, num_trials=500, seed=99
    )
    assert result_a.success_rate_pct == result_b.success_rate_pct


def test_higher_volatility_produces_wider_percentile_band():
    low_vol = run_monte_carlo_simulation(
        _base_inputs(), volatility_pct=5.0, num_trials=2000, seed=3
    )
    high_vol = run_monte_carlo_simulation(
        _base_inputs(), volatility_pct=30.0, num_trials=2000, seed=3
    )
    low_band = (low_vol.yearly_df["p90"] - low_vol.yearly_df["p10"]).iloc[-1]
    high_band = (high_vol.yearly_df["p90"] - high_vol.yearly_df["p10"]).iloc[-1]
    assert high_band > low_band