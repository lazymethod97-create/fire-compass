from services.fire_engine import FireInput, run_fire_simulation


def test_basic_simulation():
    result = run_fire_simulation(
        FireInput(
            current_age=43,
            end_age=90,
            total_assets=4700,
            cash_assets=800,
            annual_spending=200,
            annual_side_income=36,
            expected_return_pct=4,
            inflation_pct=2,
            safety_margin_pct=10,
        )
    )

    assert result.net_annual_spending == 164
    assert round(result.recommended_monthly_spending, 2) == 12.3
    assert result.cash_months > 50
    assert not result.yearly_df.empty


def test_rejects_invalid_cash():
    try:
        run_fire_simulation(
            FireInput(
                current_age=43,
                end_age=90,
                total_assets=1000,
                cash_assets=1200,
                annual_spending=200,
                annual_side_income=0,
                expected_return_pct=4,
                inflation_pct=2,
                safety_margin_pct=10,
            )
        )
        assert False
    except ValueError:
        assert True
