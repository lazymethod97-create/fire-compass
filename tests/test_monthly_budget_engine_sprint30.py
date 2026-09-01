import pytest

from services.action_engine import calculate_monthly_action
from services.fire_engine import FireInput, run_fire_simulation
from services.monthly_budget_engine import calculate_monthly_budget


@pytest.fixture
def fire_and_action():
    fire_result = run_fire_simulation(
        FireInput(
            current_age=45,
            end_age=90,
            total_assets=4700.0,
            cash_assets=800.0,
            annual_spending=200.0,
            annual_side_income=36.0,
            expected_return_pct=4.0,
            inflation_pct=2.0,
            safety_margin_pct=10.0,
        )
    )
    action_result = calculate_monthly_action(
        cash_assets=800.0,
        total_assets=4700.0,
        net_annual_spending=fire_result.net_annual_spending,
        min_cash_months=12.0,
    )
    return fire_result, action_result


def test_default_monthly_social_insurance_is_backward_compatible(fire_and_action):
    fire_result, action_result = fire_and_action

    without_param = calculate_monthly_budget(fire_result, action_result)
    with_default_zero = calculate_monthly_budget(
        fire_result, action_result, monthly_social_insurance=0.0
    )

    assert without_param.safe_monthly == with_default_zero.safe_monthly
    assert without_param.recommended_monthly == with_default_zero.recommended_monthly
    assert without_param.max_monthly == with_default_zero.max_monthly
    assert without_param.status == with_default_zero.status
    assert "social_insurance_deducted" not in without_param.reasons
    assert "social_insurance_deducted" not in with_default_zero.reasons


def test_monthly_social_insurance_is_subtracted_from_all_three_amounts(
    fire_and_action,
):
    fire_result, action_result = fire_and_action

    baseline = calculate_monthly_budget(fire_result, action_result)
    result = calculate_monthly_budget(
        fire_result, action_result, monthly_social_insurance=5.0
    )

    assert result.safe_monthly == round(max(baseline.safe_monthly - 5.0, 0.0), 2)
    assert result.recommended_monthly == round(
        max(baseline.recommended_monthly - 5.0, 0.0), 2
    )
    assert result.max_monthly == round(max(baseline.max_monthly - 5.0, 0.0), 2)
    assert "social_insurance_deducted" in result.reasons


def test_monthly_social_insurance_floors_at_zero(fire_and_action):
    fire_result, action_result = fire_and_action

    result = calculate_monthly_budget(
        fire_result, action_result, monthly_social_insurance=99999.0
    )

    assert result.safe_monthly == 0.0
    assert result.recommended_monthly == 0.0
    assert result.max_monthly == 0.0


def test_monthly_social_insurance_does_not_change_guardrail_status(fire_and_action):
    fire_result, action_result = fire_and_action

    baseline = calculate_monthly_budget(fire_result, action_result)
    result = calculate_monthly_budget(
        fire_result, action_result, monthly_social_insurance=5.0
    )

    assert result.status == baseline.status


def test_negative_monthly_social_insurance_raises_value_error(fire_and_action):
    fire_result, action_result = fire_and_action

    with pytest.raises(ValueError):
        calculate_monthly_budget(
            fire_result, action_result, monthly_social_insurance=-1.0
        )


def test_monthly_social_insurance_combines_with_other_factors(fire_and_action):
    fire_result, action_result = fire_and_action

    result = calculate_monthly_budget(
        fire_result,
        action_result,
        market_crash=True,
        monthly_social_insurance=3.0,
    )

    assert "market_crash_active" in result.reasons
    assert "social_insurance_deducted" in result.reasons
    assert result.status == "red"
