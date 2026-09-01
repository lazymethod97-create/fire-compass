import pytest

from services.social_insurance_engine import (
    BASIC_DEDUCTION,
    NATIONAL_PENSION_MONTHLY_FEE,
    calculate_social_insurance,
)


def test_zero_income_single_household_still_charges_per_capita_levy():
    """所得0でも均等割分は発生する（軽減制度は考慮しない設計）。"""
    result = calculate_social_insurance(
        prior_year_income=0.0, household_size=1, current_age=45
    )

    assert result.taxable_base == 0.0
    assert result.annual_health_insurance > 0.0
    for component in result.health_insurance_components:
        assert component.income_levy == 0.0
        assert component.per_capita_levy > 0.0


def test_income_levy_applies_after_basic_deduction():
    result = calculate_social_insurance(
        prior_year_income=500.0, household_size=1, current_age=45
    )

    assert result.taxable_base == round(500.0 - BASIC_DEDUCTION, 2)
    for component in result.health_insurance_components:
        assert component.income_levy > 0.0


def test_care_portion_included_for_ages_40_to_64():
    result_39 = calculate_social_insurance(
        prior_year_income=500.0, household_size=1, current_age=39
    )
    result_40 = calculate_social_insurance(
        prior_year_income=500.0, household_size=1, current_age=40
    )
    result_64 = calculate_social_insurance(
        prior_year_income=500.0, household_size=1, current_age=64
    )
    result_65 = calculate_social_insurance(
        prior_year_income=500.0, household_size=1, current_age=65
    )

    labels_39 = [c.label for c in result_39.health_insurance_components]
    labels_40 = [c.label for c in result_40.health_insurance_components]
    labels_64 = [c.label for c in result_64.health_insurance_components]
    labels_65 = [c.label for c in result_65.health_insurance_components]

    assert "介護分" not in labels_39
    assert "介護分" in labels_40
    assert "介護分" in labels_64
    assert "介護分" not in labels_65


def test_national_pension_applicable_ages_20_to_59():
    result_19 = calculate_social_insurance(
        prior_year_income=0.0, household_size=1, current_age=19
    )
    result_20 = calculate_social_insurance(
        prior_year_income=0.0, household_size=1, current_age=20
    )
    result_59 = calculate_social_insurance(
        prior_year_income=0.0, household_size=1, current_age=59
    )
    result_60 = calculate_social_insurance(
        prior_year_income=0.0, household_size=1, current_age=60
    )

    assert result_19.national_pension_applicable is False
    assert result_19.monthly_national_pension == 0.0

    assert result_20.national_pension_applicable is True
    assert result_20.monthly_national_pension == round(
        NATIONAL_PENSION_MONTHLY_FEE, 2
    )

    assert result_59.national_pension_applicable is True
    assert result_60.national_pension_applicable is False
    assert result_60.monthly_national_pension == 0.0


def test_household_size_increases_per_capita_levy_only():
    result_1 = calculate_social_insurance(
        prior_year_income=500.0, household_size=1, current_age=45
    )
    result_3 = calculate_social_insurance(
        prior_year_income=500.0, household_size=3, current_age=45
    )

    for c1, c3 in zip(
        result_1.health_insurance_components,
        result_3.health_insurance_components,
    ):
        assert c1.income_levy == c3.income_levy
        assert c3.per_capita_levy == round(c1.per_capita_levy * 3, 2)

    assert result_3.annual_health_insurance > result_1.annual_health_insurance


def test_cap_is_applied_for_very_high_income():
    result = calculate_social_insurance(
        prior_year_income=5000.0, household_size=1, current_age=45
    )

    for component in result.health_insurance_components:
        assert component.capped_amount <= component.subtotal
        if component.capped:
            assert component.capped_amount < component.subtotal


def test_monthly_total_is_annual_total_divided_by_twelve():
    result = calculate_social_insurance(
        prior_year_income=500.0, household_size=1, current_age=45
    )

    assert result.monthly_total == round(result.annual_total / 12.0, 2)
    assert result.annual_total == round(
        result.annual_health_insurance + result.annual_national_pension, 2
    )


@pytest.mark.parametrize(
    "prior_year_income,household_size,current_age",
    [(-1.0, 1, 45), (500.0, 0, 45), (500.0, 1, -1)],
)
def test_invalid_inputs_raise_value_error(
    prior_year_income, household_size, current_age
):
    with pytest.raises(ValueError):
        calculate_social_insurance(
            prior_year_income=prior_year_income,
            household_size=household_size,
            current_age=current_age,
        )


def test_notes_mention_approximation_disclaimer():
    result = calculate_social_insurance(
        prior_year_income=500.0, household_size=1, current_age=45
    )
    assert any("目安" in note for note in result.notes)
