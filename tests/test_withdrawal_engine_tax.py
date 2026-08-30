import pytest

from services.withdrawal_engine import (
    TAXABLE_CAPITAL_GAINS_TAX_RATE,
    calculate_withdrawal_plan,
)


def _base_kwargs(**overrides):
    kwargs = dict(
        amount_needed=30.0,
        cash_assets=50.0,
        cash_buffer_target=200.0,
        taxable_assets=100.0,
        nisa_assets=50.0,
        ideco_assets=0.0,
        current_age=62,
        ideco_access_age=60,
        pension_start_age=70,
        pension_monthly_income=0.0,
    )
    kwargs.update(overrides)
    return kwargs


def _taxable_step(plan):
    return next(step for step in plan.steps if step.source == "課税口座")


def test_default_taxable_gain_ratio_behaves_like_before():
    plan = calculate_withdrawal_plan(**_base_kwargs())
    step = _taxable_step(plan)

    assert step.amount == 30.0
    assert step.estimated_tax == 0.0
    assert step.gross_sell_amount is None
    assert plan.total_estimated_tax == 0.0
    assert "含み益" not in step.reason


def test_taxable_gain_ratio_zero_explicit_behaves_like_default():
    plan = calculate_withdrawal_plan(
        **_base_kwargs(taxable_gain_ratio=0.0)
    )
    step = _taxable_step(plan)

    assert step.estimated_tax == 0.0
    assert step.gross_sell_amount is None


def test_taxable_gain_ratio_applies_estimated_tax():
    plan = calculate_withdrawal_plan(
        **_base_kwargs(taxable_gain_ratio=0.4)
    )
    step = _taxable_step(plan)

    expected_tax = round(30.0 * 0.4 * TAXABLE_CAPITAL_GAINS_TAX_RATE, 2)
    expected_gross = round(30.0 + expected_tax, 2)

    assert step.amount == 30.0  # 純額（今月の資金繰りに使う額）は変わらない
    assert step.estimated_tax == expected_tax
    assert step.gross_sell_amount == expected_gross
    assert plan.total_estimated_tax == expected_tax
    assert "含み益" in step.reason


def test_full_gain_ratio_applies_full_tax_rate():
    plan = calculate_withdrawal_plan(
        **_base_kwargs(taxable_gain_ratio=1.0)
    )
    step = _taxable_step(plan)

    expected_tax = round(30.0 * TAXABLE_CAPITAL_GAINS_TAX_RATE, 2)

    assert step.estimated_tax == expected_tax
    assert step.gross_sell_amount == round(30.0 + expected_tax, 2)


def test_other_steps_are_unaffected_by_taxable_gain_ratio():
    plan = calculate_withdrawal_plan(
        **_base_kwargs(
            amount_needed=500.0,
            cash_assets=250.0,
            cash_buffer_target=200.0,
            taxable_gain_ratio=0.5,
        )
    )

    for step in plan.steps:
        if step.source != "課税口座":
            assert step.estimated_tax == 0.0
            assert step.gross_sell_amount is None


def test_total_estimated_tax_matches_sum_of_steps():
    plan = calculate_withdrawal_plan(
        **_base_kwargs(taxable_gain_ratio=0.3)
    )

    assert plan.total_estimated_tax == round(
        sum(step.estimated_tax for step in plan.steps), 2
    )


def test_negative_gain_ratio_raises():
    with pytest.raises(ValueError):
        calculate_withdrawal_plan(
            **_base_kwargs(taxable_gain_ratio=-0.1)
        )


def test_gain_ratio_above_one_raises():
    with pytest.raises(ValueError):
        calculate_withdrawal_plan(
            **_base_kwargs(taxable_gain_ratio=1.1)
        )


def test_no_tax_impact_when_taxable_step_not_triggered():
    # 現金だけで足りる場合、課税口座ステップ自体が発生しない
    plan = calculate_withdrawal_plan(
        **_base_kwargs(
            amount_needed=10.0,
            cash_assets=300.0,
            cash_buffer_target=200.0,
            taxable_gain_ratio=0.5,
        )
    )

    assert not any(step.source == "課税口座" for step in plan.steps)
    assert plan.total_estimated_tax == 0.0


def test_total_covered_and_shortfall_unaffected_by_tax_fields():
    plan_no_tax = calculate_withdrawal_plan(**_base_kwargs())
    plan_with_tax = calculate_withdrawal_plan(
        **_base_kwargs(taxable_gain_ratio=0.6)
    )

    assert plan_no_tax.total_covered == plan_with_tax.total_covered
    assert plan_no_tax.shortfall_uncovered == plan_with_tax.shortfall_uncovered
