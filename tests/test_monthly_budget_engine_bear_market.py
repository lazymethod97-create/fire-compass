import pytest

from services.action_engine import calculate_monthly_action
from services.fire_engine import FireInput, run_fire_simulation
from services.monthly_budget_engine import calculate_monthly_budget


@pytest.fixture
def healthy_fire_and_action():
    """悲観ケースでも枯渇せず、現金バッファも十分な「健全」ケース。
    bear_marketの効果だけを切り分けて確認するためのフィクスチャ。
    """
    fire_result = run_fire_simulation(
        FireInput(
            current_age=45,
            end_age=90,
            total_assets=15000.0,
            cash_assets=1200.0,
            annual_spending=200.0,
            annual_side_income=36.0,
            expected_return_pct=4.0,
            inflation_pct=2.0,
            safety_margin_pct=10.0,
        )
    )
    action_result = calculate_monthly_action(
        cash_assets=1200.0,
        total_assets=15000.0,
        net_annual_spending=fire_result.net_annual_spending,
        min_cash_months=12.0,
    )
    return fire_result, action_result


def test_default_bear_market_is_backward_compatible(healthy_fire_and_action):
    fire_result, action_result = healthy_fire_and_action

    without_param = calculate_monthly_budget(fire_result, action_result)
    with_default_false = calculate_monthly_budget(
        fire_result, action_result, bear_market=False
    )

    assert without_param.safe_monthly == with_default_false.safe_monthly
    assert without_param.max_monthly == with_default_false.max_monthly
    assert without_param.status == with_default_false.status
    assert "bear_market_active" not in without_param.reasons


def test_bear_market_reduces_safe_and_max_monthly(healthy_fire_and_action):
    fire_result, action_result = healthy_fire_and_action

    baseline = calculate_monthly_budget(fire_result, action_result)
    result = calculate_monthly_budget(fire_result, action_result, bear_market=True)

    assert result.safe_monthly < baseline.safe_monthly
    assert result.max_monthly < baseline.max_monthly
    assert "bear_market_active" in result.reasons
    assert "upside_allowed" not in result.reasons
    assert result.binding_safe_factor_reason == "bear_market_active"


def test_bear_market_downgrades_status_to_yellow(healthy_fire_and_action):
    fire_result, action_result = healthy_fire_and_action

    baseline = calculate_monthly_budget(fire_result, action_result)
    result = calculate_monthly_budget(fire_result, action_result, bear_market=True)

    assert baseline.status == "green"
    assert result.status == "yellow"


def test_market_crash_takes_priority_over_bear_market(healthy_fire_and_action):
    fire_result, action_result = healthy_fire_and_action

    result = calculate_monthly_budget(
        fire_result, action_result, market_crash=True, bear_market=True
    )

    assert result.status == "red"
    assert "market_crash_active" in result.reasons
    assert "bear_market_active" not in result.reasons
    assert result.binding_safe_factor_reason == "market_crash_active"


def test_cash_shortage_takes_priority_over_bear_market():
    fire_result = run_fire_simulation(
        FireInput(
            current_age=45,
            end_age=90,
            total_assets=15000.0,
            cash_assets=50.0,
            annual_spending=200.0,
            annual_side_income=36.0,
            expected_return_pct=4.0,
            inflation_pct=2.0,
            safety_margin_pct=10.0,
        )
    )
    action_result = calculate_monthly_action(
        cash_assets=50.0,
        total_assets=15000.0,
        net_annual_spending=fire_result.net_annual_spending,
        min_cash_months=12.0,
    )

    result = calculate_monthly_budget(
        fire_result, action_result, bear_market=True
    )

    assert "cash_buffer_below_target" in result.reasons
    assert "bear_market_active" not in result.reasons
    assert result.binding_safe_factor_reason == "cash_buffer_below_target"


def test_bear_market_combines_with_social_insurance(healthy_fire_and_action):
    fire_result, action_result = healthy_fire_and_action

    result = calculate_monthly_budget(
        fire_result,
        action_result,
        bear_market=True,
        monthly_social_insurance=3.0,
    )

    assert "bear_market_active" in result.reasons
    assert "social_insurance_deducted" in result.reasons
