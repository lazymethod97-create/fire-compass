import pandas as pd
import pytest

from services.fire_engine import FireResult, ScenarioSummary
from services.action_engine import ActionResult
from services.monthly_budget_engine import calculate_monthly_budget


def _make_fire_result(bear_depletes: bool) -> FireResult:
    scenarios = [
        ScenarioSummary(
            name="標準ケース", final_assets=1000.0, min_assets=500.0,
            depleted_at="期間内に枯渇せず",
        ),
        ScenarioSummary(
            name="悲観ケース", final_assets=0.0, min_assets=0.0,
            depleted_at="78歳頃" if bear_depletes else "期間内に枯渇せず",
        ),
        ScenarioSummary(
            name="楽観ケース", final_assets=2000.0, min_assets=800.0,
            depleted_at="期間内に枯渇せず",
        ),
    ]
    return FireResult(
        net_annual_spending=240.0,
        recommended_monthly_spending=18.0,
        cash_months=10.0,
        asset_depletion_label="計画的な取り崩し",
        advice="",
        yearly_df=pd.DataFrame({"age": [60], "standard": [1000.0], "bear": [0.0], "bull": [2000.0]}),
        scenario_summaries=scenarios,
    )


def _make_action_result(cash_shortage: float, target_cash_amount: float = 200.0) -> ActionResult:
    return ActionResult(
        target_cash_amount=target_cash_amount,
        target_cash_months=12.0,
        cash_surplus=0.0 if cash_shortage > 0 else 50.0,
        cash_shortage=cash_shortage,
        additional_investment=0.0,
        investment_withdrawal=cash_shortage,
        action="",
        reason="",
    )


def test_healthy_case_is_green_and_allows_upside():
    result = calculate_monthly_budget(
        _make_fire_result(bear_depletes=False),
        _make_action_result(cash_shortage=0.0),
    )
    assert result.status == "green"
    assert result.safe_monthly == result.recommended_monthly
    assert result.max_monthly > result.recommended_monthly
    assert "cash_buffer_healthy" in result.reasons


def test_cash_shortage_is_yellow_and_tightens_safe_only():
    result = calculate_monthly_budget(
        _make_fire_result(bear_depletes=False),
        _make_action_result(cash_shortage=40.0),
    )
    assert result.status == "yellow"
    assert result.safe_monthly < result.recommended_monthly
    assert result.max_monthly == result.recommended_monthly
    assert "cash_buffer_below_target" in result.reasons


def test_bear_case_depletion_forces_red_regardless_of_cash():
    result = calculate_monthly_budget(
        _make_fire_result(bear_depletes=True),
        _make_action_result(cash_shortage=0.0),
    )
    assert result.status == "red"
    assert result.safe_monthly < result.recommended_monthly
    assert "bear_case_depletes" in result.reasons


def test_market_crash_overrides_everything_to_red_and_tightest_safe():
    healthy_result = calculate_monthly_budget(
        _make_fire_result(bear_depletes=False),
        _make_action_result(cash_shortage=0.0),
        market_crash=True,
    )
    bear_result = calculate_monthly_budget(
        _make_fire_result(bear_depletes=True),
        _make_action_result(cash_shortage=40.0),
        market_crash=True,
    )
    assert healthy_result.status == "red"
    assert bear_result.status == "red"
    # 暴落フラグが立っている場合、悲観ケース枯渇より厳しい係数になる
    assert healthy_result.safe_monthly <= bear_result.safe_monthly


def test_zero_target_cash_amount_does_not_divide_by_zero():
    result = calculate_monthly_budget(
        _make_fire_result(bear_depletes=False),
        _make_action_result(cash_shortage=0.0, target_cash_amount=0.0),
    )
    assert result.status == "green"


def test_default_upcoming_large_expense_matches_previous_behavior():
    baseline = calculate_monthly_budget(
        _make_fire_result(bear_depletes=False),
        _make_action_result(cash_shortage=0.0),
    )
    explicit_zero = calculate_monthly_budget(
        _make_fire_result(bear_depletes=False),
        _make_action_result(cash_shortage=0.0),
        upcoming_large_expense=0.0,
    )
    assert baseline == explicit_zero


def test_large_expense_within_cash_surplus_does_not_downgrade_status():
    # _make_action_result(cash_shortage=0.0)のcash_surplusは50.0
    result = calculate_monthly_budget(
        _make_fire_result(bear_depletes=False),
        _make_action_result(cash_shortage=0.0),
        upcoming_large_expense=30.0,
    )
    assert result.status == "green"
    assert "large_expense_within_cash_surplus" in result.reasons
    assert "large_expense_exceeds_cash_surplus" not in result.reasons


def test_large_expense_exceeding_cash_surplus_downgrades_green_to_yellow():
    result = calculate_monthly_budget(
        _make_fire_result(bear_depletes=False),
        _make_action_result(cash_shortage=0.0),
        upcoming_large_expense=80.0,
    )
    assert result.status == "yellow"
    assert "large_expense_exceeds_cash_surplus" in result.reasons


def test_large_expense_does_not_change_safe_or_max_monthly_amounts():
    without_expense = calculate_monthly_budget(
        _make_fire_result(bear_depletes=False),
        _make_action_result(cash_shortage=0.0),
    )
    with_expense = calculate_monthly_budget(
        _make_fire_result(bear_depletes=False),
        _make_action_result(cash_shortage=0.0),
        upcoming_large_expense=80.0,
    )
    assert with_expense.safe_monthly == without_expense.safe_monthly
    assert with_expense.max_monthly == without_expense.max_monthly


def test_large_expense_does_not_upgrade_existing_red_status():
    result = calculate_monthly_budget(
        _make_fire_result(bear_depletes=True),
        _make_action_result(cash_shortage=0.0),
        upcoming_large_expense=80.0,
    )
    assert result.status == "red"
    assert "large_expense_exceeds_cash_surplus" in result.reasons


def test_large_expense_does_not_upgrade_existing_yellow_status():
    result = calculate_monthly_budget(
        _make_fire_result(bear_depletes=False),
        _make_action_result(cash_shortage=40.0),
        upcoming_large_expense=80.0,
    )
    assert result.status == "yellow"
    assert "large_expense_exceeds_cash_surplus" in result.reasons


def test_negative_upcoming_large_expense_raises_value_error():
    with pytest.raises(ValueError):
        calculate_monthly_budget(
            _make_fire_result(bear_depletes=False),
            _make_action_result(cash_shortage=0.0),
            upcoming_large_expense=-1.0,
        )
