from services.crash_strategy import calculate_crash_strategy

def test_normal():
    r = calculate_crash_strategy(12.3, 12, "通常")
    assert r.target_cash_months == 12
    assert r.additional_investment_ratio == 1.0
    assert r.recommended_monthly_spending == 12.3

def test_bear():
    r = calculate_crash_strategy(12.3, 12, "弱気相場")
    assert r.target_cash_months == 15
    assert r.additional_investment_ratio == 0.5
    assert r.spending_reduction_pct == 5
    assert r.recommended_monthly_spending == 11.69

def test_crash():
    r = calculate_crash_strategy(12.3, 12, "暴落")
    assert r.target_cash_months == 18
    assert r.additional_investment_ratio == 0
    assert r.spending_reduction_pct == 10
    assert r.recommended_monthly_spending == 11.07

def test_severe_crash():
    r = calculate_crash_strategy(12.3, 12, "深刻な暴落")
    assert r.target_cash_months == 24
    assert r.additional_investment_ratio == 0
    assert r.spending_reduction_pct == 15
    assert r.recommended_monthly_spending == 10.46
