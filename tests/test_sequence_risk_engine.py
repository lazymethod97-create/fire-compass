import pytest

from services.sequence_risk_engine import (
    HISTORICAL_ANNUAL_RETURNS_PCT,
    SequenceRiskResult,
    calculate_sequence_risk_factor,
)


def test_returns_neutral_factor_outside_early_retirement_stage_before_60():
    result = calculate_sequence_risk_factor(
        current_age=45,
        pension_start_age=65,
        total_assets=3000.0,
        annual_spending=250.0,
        annual_side_income=0.0,
        expected_return_pct=4.0,
        inflation_pct=2.0,
    )

    assert result.life_stage_applicable is False
    assert result.risk_factor == 1.00
    assert result.bad_path_ratio == 0.0
    assert "not_early_retirement_stage" in result.reasons


def test_returns_neutral_factor_after_pension_start():
    result = calculate_sequence_risk_factor(
        current_age=72,
        pension_start_age=65,
        total_assets=3000.0,
        annual_spending=250.0,
        annual_side_income=0.0,
        expected_return_pct=4.0,
        inflation_pct=2.0,
    )

    assert result.life_stage_applicable is False
    assert result.risk_factor == 1.00


def test_evaluates_when_in_early_retirement_stage():
    result = calculate_sequence_risk_factor(
        current_age=62,
        pension_start_age=70,
        total_assets=3000.0,
        annual_spending=250.0,
        annual_side_income=0.0,
        expected_return_pct=4.0,
        inflation_pct=2.0,
        random_seed=42,
    )

    assert result.life_stage_applicable is True
    assert "early_retirement_stage_evaluated" in result.reasons


def test_ample_assets_yield_neutral_factor():
    result = calculate_sequence_risk_factor(
        current_age=62,
        pension_start_age=70,
        total_assets=20000.0,
        annual_spending=200.0,
        annual_side_income=36.0,
        expected_return_pct=4.0,
        inflation_pct=2.0,
        random_seed=42,
    )

    assert result.risk_factor == 1.00
    assert result.bad_path_ratio == 0.0


def test_thin_assets_yield_stricter_factor():
    result = calculate_sequence_risk_factor(
        current_age=62,
        pension_start_age=70,
        total_assets=2000.0,
        annual_spending=300.0,
        annual_side_income=0.0,
        expected_return_pct=4.0,
        inflation_pct=2.0,
        random_seed=42,
    )

    assert result.risk_factor < 1.00
    assert result.bad_path_ratio > 0.0
    assert "sequence_risk_elevated" in result.reasons


def test_same_seed_is_reproducible():
    kwargs = dict(
        current_age=63,
        pension_start_age=68,
        total_assets=2500.0,
        annual_spending=260.0,
        annual_side_income=0.0,
        expected_return_pct=3.0,
        inflation_pct=2.0,
        random_seed=123,
    )

    result_a = calculate_sequence_risk_factor(**kwargs)
    result_b = calculate_sequence_risk_factor(**kwargs)

    assert result_a.bad_path_ratio == result_b.bad_path_ratio
    assert result_a.risk_factor == result_b.risk_factor


def test_no_net_withdrawal_needed_when_side_income_covers_spending():
    result = calculate_sequence_risk_factor(
        current_age=62,
        pension_start_age=70,
        total_assets=1000.0,
        annual_spending=100.0,
        annual_side_income=200.0,
        expected_return_pct=4.0,
        inflation_pct=2.0,
    )

    assert result.risk_factor == 1.00
    assert "no_net_withdrawal_needed" in result.reasons


def test_risk_factor_is_bounded_within_known_thresholds():
    result = calculate_sequence_risk_factor(
        current_age=61,
        pension_start_age=69,
        total_assets=100.0,
        annual_spending=500.0,
        annual_side_income=0.0,
        expected_return_pct=4.0,
        inflation_pct=2.0,
        random_seed=1,
    )

    assert result.risk_factor in (0.85, 0.90, 0.95, 1.00)
    assert result.risk_factor <= 0.90  # 極端に不利な条件では厳しい係数になる


@pytest.mark.parametrize(
    "current_age,pension_start_age",
    [
        (59, 65),  # 60歳未満は対象外
        (65, 65),  # 受給開始年齢と同じ = 受給中扱いで対象外
    ],
)
def test_boundary_ages_are_not_early_retirement_stage(
    current_age, pension_start_age
):
    result = calculate_sequence_risk_factor(
        current_age=current_age,
        pension_start_age=pension_start_age,
        total_assets=3000.0,
        annual_spending=250.0,
        annual_side_income=0.0,
        expected_return_pct=4.0,
        inflation_pct=2.0,
    )

    assert result.life_stage_applicable is False


def test_negative_current_age_raises():
    with pytest.raises(ValueError):
        calculate_sequence_risk_factor(
            current_age=-1,
            pension_start_age=65,
            total_assets=3000.0,
            annual_spending=250.0,
            annual_side_income=0.0,
            expected_return_pct=4.0,
            inflation_pct=2.0,
        )


def test_negative_total_assets_raises():
    with pytest.raises(ValueError):
        calculate_sequence_risk_factor(
            current_age=62,
            pension_start_age=70,
            total_assets=-100.0,
            annual_spending=250.0,
            annual_side_income=0.0,
            expected_return_pct=4.0,
            inflation_pct=2.0,
        )


def test_zero_simulations_raises():
    with pytest.raises(ValueError):
        calculate_sequence_risk_factor(
            current_age=62,
            pension_start_age=70,
            total_assets=3000.0,
            annual_spending=250.0,
            annual_side_income=0.0,
            expected_return_pct=4.0,
            inflation_pct=2.0,
            n_simulations=0,
        )


def test_window_years_too_long_raises():
    with pytest.raises(ValueError):
        calculate_sequence_risk_factor(
            current_age=62,
            pension_start_age=70,
            total_assets=3000.0,
            annual_spending=250.0,
            annual_side_income=0.0,
            expected_return_pct=4.0,
            inflation_pct=2.0,
            window_years=10_000,
        )


def test_historical_returns_dataset_is_nonempty_and_reasonable():
    assert len(HISTORICAL_ANNUAL_RETURNS_PCT) >= 30
    assert all(isinstance(r, float) for r in HISTORICAL_ANNUAL_RETURNS_PCT)
    # 極端に非現実的な値が混入していないことの簡易チェック
    assert all(-60.0 < r < 60.0 for r in HISTORICAL_ANNUAL_RETURNS_PCT)


def test_result_is_dataclass_instance():
    result = calculate_sequence_risk_factor(
        current_age=62,
        pension_start_age=70,
        total_assets=3000.0,
        annual_spending=250.0,
        annual_side_income=0.0,
        expected_return_pct=4.0,
        inflation_pct=2.0,
    )
    assert isinstance(result, SequenceRiskResult)
