from services.withdrawal_engine import calculate_withdrawal_plan


def test_covered_entirely_by_cash_within_buffer():
    result = calculate_withdrawal_plan(
        amount_needed=10.0,
        cash_assets=100.0,
        cash_buffer_target=50.0,
        taxable_assets=200.0,
        nisa_assets=100.0,
        ideco_assets=100.0,
        current_age=50,
        ideco_access_age=60,
        pension_start_age=65,
        pension_monthly_income=0.0,
    )
    assert result.total_covered == 10.0
    assert result.shortfall_uncovered == 0.0
    assert len(result.steps) == 1
    assert result.steps[0].source == "現金"
    assert not result.dipped_into_cash_buffer


def test_pension_used_before_taxable_when_eligible():
    result = calculate_withdrawal_plan(
        amount_needed=30.0,
        cash_assets=50.0,
        cash_buffer_target=50.0,  # 現金の余剰なし
        taxable_assets=200.0,
        nisa_assets=100.0,
        ideco_assets=100.0,
        current_age=66,
        ideco_access_age=60,
        pension_start_age=65,
        pension_monthly_income=15.0,
    )
    sources = [s.source for s in result.steps]
    assert sources[0] == "年金"
    assert sources[1] == "課税口座"
    assert result.total_covered == 30.0


def test_ideco_excluded_before_access_age():
    result = calculate_withdrawal_plan(
        amount_needed=500.0,
        cash_assets=0.0,
        cash_buffer_target=0.0,
        taxable_assets=0.0,
        nisa_assets=0.0,
        ideco_assets=300.0,
        current_age=45,
        ideco_access_age=60,
        pension_start_age=65,
        pension_monthly_income=0.0,
    )
    ideco_step = next(s for s in result.steps if "iDeCo" in s.source)
    assert ideco_step.source == "iDeCo（利用不可）"
    assert ideco_step.amount == 0.0
    assert result.shortfall_uncovered == 500.0


def test_ideco_used_after_access_age():
    result = calculate_withdrawal_plan(
        amount_needed=50.0,
        cash_assets=0.0,
        cash_buffer_target=0.0,
        taxable_assets=0.0,
        nisa_assets=0.0,
        ideco_assets=300.0,
        current_age=61,
        ideco_access_age=60,
        pension_start_age=65,
        pension_monthly_income=0.0,
    )
    ideco_step = next(s for s in result.steps if s.source == "iDeCo")
    assert ideco_step.amount == 50.0
    assert result.shortfall_uncovered == 0.0


def test_dips_into_cash_buffer_as_last_resort():
    result = calculate_withdrawal_plan(
        amount_needed=20.0,
        cash_assets=50.0,
        cash_buffer_target=50.0,
        taxable_assets=0.0,
        nisa_assets=0.0,
        ideco_assets=0.0,
        current_age=50,
        ideco_access_age=60,
        pension_start_age=65,
        pension_monthly_income=0.0,
    )
    assert result.dipped_into_cash_buffer
    assert result.steps[-1].source == "現金（バッファ割れ）"
    assert result.total_covered == 20.0


def test_taxable_order_before_nisa():
    result = calculate_withdrawal_plan(
        amount_needed=100.0,
        cash_assets=0.0,
        cash_buffer_target=0.0,
        taxable_assets=60.0,
        nisa_assets=200.0,
        ideco_assets=0.0,
        current_age=50,
        ideco_access_age=60,
        pension_start_age=65,
        pension_monthly_income=0.0,
    )
    assert result.steps[0].source == "課税口座"
    assert result.steps[0].amount == 60.0
    assert result.steps[1].source == "NISA"
    assert result.steps[1].amount == 40.0
