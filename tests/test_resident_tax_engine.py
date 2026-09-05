import pytest

from services.resident_tax_engine import (
    BASIC_DEDUCTION,
    INCOME_LEVY_RATE,
    PER_CAPITA_LEVY,
    calculate_resident_tax,
)


def test_zero_income_still_charges_per_capita_levy():
    result = calculate_resident_tax(0.0)

    assert result.taxable_base == 0.0
    assert result.income_levy == 0.0
    assert result.per_capita_levy == PER_CAPITA_LEVY
    assert result.annual_total == PER_CAPITA_LEVY


def test_income_levy_applies_after_basic_deduction():
    result = calculate_resident_tax(500.0)

    assert result.taxable_base == round(500.0 - BASIC_DEDUCTION, 2)
    assert result.income_levy == round(result.taxable_base * INCOME_LEVY_RATE, 2)
    assert result.income_levy > 0.0


def test_income_below_basic_deduction_has_zero_income_levy():
    result = calculate_resident_tax(30.0)

    assert result.taxable_base == 0.0
    assert result.income_levy == 0.0
    assert result.annual_total == PER_CAPITA_LEVY


def test_monthly_total_is_annual_total_divided_by_twelve():
    result = calculate_resident_tax(500.0)

    assert result.annual_total == round(
        result.income_levy + result.per_capita_levy, 2
    )
    assert result.monthly_total == round(result.annual_total / 12.0, 2)


def test_negative_income_raises_value_error():
    with pytest.raises(ValueError):
        calculate_resident_tax(-1.0)


def test_notes_mention_approximation_disclaimer():
    result = calculate_resident_tax(500.0)
    assert any("目安" in note for note in result.notes)
