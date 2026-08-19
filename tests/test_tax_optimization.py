from services.tax_optimization import (
    NISA_GROWTH_LIMIT,
    NISA_TOTAL_LIMIT,
    TaxOptimizationInput,
    calculate_ideco_contribution,
    calculate_nisa_room,
    calculate_pension_gap,
    run_tax_optimization,
)


def test_nisa_room_calculation():
    total, growth, annual = calculate_nisa_room(
        contributed=500.0,
        growth_contributed=300.0,
        annual_contributed=120.0,
    )
    assert total == NISA_TOTAL_LIMIT - 500.0
    assert growth == NISA_GROWTH_LIMIT - 300.0
    assert annual == 240.0


def test_nisa_room_never_becomes_negative():
    total, growth, annual = calculate_nisa_room(
        contributed=2000.0,
        growth_contributed=1500.0,
        annual_contributed=500.0,
    )
    assert total == 0.0
    assert growth == 0.0
    assert annual == 0.0


def test_ideco_is_capped_by_annual_limit():
    assert calculate_ideco_contribution(5.0, 74.4) == 60.0
    assert calculate_ideco_contribution(10.0, 74.4) == 74.4


def test_pension_gap():
    assert calculate_pension_gap(200.0, 150.0) == 50.0
    assert calculate_pension_gap(200.0, 220.0) == 0.0


def test_integrated_optimization():
    result = run_tax_optimization(
        TaxOptimizationInput(
            nisa_assets=800.0,
            nisa_contributed=600.0,
            nisa_growth_contributed=200.0,
            nisa_annual_contributed=100.0,
            taxable_assets=2800.0,
            ideco_assets=55.0,
            ideco_monthly_contribution=1.0,
            ideco_annual_limit=74.4,
            current_age=43,
            pension_start_age=65,
            annual_pension=150.0,
            annual_spending=200.0,
            end_age=90,
        )
    )

    assert result.nisa_remaining_limit == 1200.0
    assert result.nisa_growth_remaining_limit == 1000.0
    assert result.nisa_annual_room == 260.0
    assert result.ideco_annual_contribution == 12.0
    assert result.pension_annual_income == 150.0
    assert result.pension_gap_after_start == 50.0
