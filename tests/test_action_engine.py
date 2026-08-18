from services.action_engine import calculate_monthly_action


def test_recommends_additional_investment_when_cash_exceeds_buffer():
    result = calculate_monthly_action(
        cash_assets=800,
        total_assets=4700,
        net_annual_spending=164,
        min_cash_months=12,
    )

    assert round(result.target_cash_amount, 2) == round(164 / 12 * 12, 2)
    assert result.additional_investment == 636
    assert result.investment_withdrawal == 0
    assert result.action == "追加投資"


def test_recommends_withdrawal_when_cash_is_below_buffer():
    result = calculate_monthly_action(
        cash_assets=100,
        total_assets=4700,
        net_annual_spending=164,
        min_cash_months=12,
    )

    assert round(result.investment_withdrawal, 2) == 64
    assert result.additional_investment == 0
    assert result.action == "投資信託を取り崩して現金を補充"


def test_recommends_no_action_when_cash_matches_buffer():
    result = calculate_monthly_action(
        cash_assets=164,
        total_assets=4700,
        net_annual_spending=164,
        min_cash_months=12,
    )

    assert result.additional_investment == 0
    assert result.investment_withdrawal == 0
    assert result.action == "取り崩し・追加投資は不要"


def test_withdrawal_is_capped_by_investment_assets():
    result = calculate_monthly_action(
        cash_assets=300,
        total_assets=300,
        net_annual_spending=164,
        min_cash_months=36,
    )

    assert result.investment_withdrawal == 0
    assert result.action == "現金バッファ不足"
