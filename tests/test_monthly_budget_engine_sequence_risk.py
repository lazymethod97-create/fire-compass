from services.action_engine import ActionResult
from services.fire_engine import FireResult, ScenarioSummary
from services.monthly_budget_engine import calculate_monthly_budget


def _healthy_fire_result(recommended_monthly=20.0):
    return FireResult(
        net_annual_spending=240.0,
        recommended_monthly_spending=recommended_monthly,
        cash_months=15.0,
        asset_depletion_label="余裕あり",
        advice="",
        yearly_df=None,
        scenario_summaries=[
            ScenarioSummary("標準ケース", 5000.0, 3000.0, "期間内に枯渇せず"),
            ScenarioSummary("悲観ケース", 3000.0, 1000.0, "期間内に枯渇せず"),
            ScenarioSummary("楽観ケース", 7000.0, 5000.0, "期間内に枯渇せず"),
        ],
    )


def _healthy_action_result():
    return ActionResult(
        target_cash_amount=200.0,
        target_cash_months=12.0,
        cash_surplus=50.0,
        cash_shortage=0.0,
        additional_investment=50.0,
        investment_withdrawal=0.0,
        action="追加投資",
        reason="",
    )


def test_sequence_risk_factor_ignored_outside_early_retirement_stage():
    # current_age/pension_start_ageが未指定 = ステージ判定なし
    result = calculate_monthly_budget(
        fire_result=_healthy_fire_result(),
        action_result=_healthy_action_result(),
        sequence_risk_factor=0.80,
    )

    assert "sequence_risk_evaluated" not in result.reasons
    assert result.safe_monthly == round(20.0 * 1.00, 2)


def test_sequence_risk_factor_ignored_in_late_stage():
    result = calculate_monthly_budget(
        fire_result=_healthy_fire_result(),
        action_result=_healthy_action_result(),
        current_age=80,
        pension_start_age=65,
        sequence_risk_factor=0.80,
    )

    assert "sequence_risk_evaluated" not in result.reasons
    assert "late_stage_conservative" in result.reasons
    assert result.safe_monthly == round(20.0 * 0.90, 2)


def test_sequence_risk_factor_applied_when_stricter_in_early_retirement():
    result = calculate_monthly_budget(
        fire_result=_healthy_fire_result(),
        action_result=_healthy_action_result(),
        current_age=62,
        pension_start_age=70,
        sequence_risk_factor=0.85,
    )

    assert "sequence_risk_evaluated" in result.reasons
    assert "sequence_risk_applied" in result.reasons
    # 0.85 (系列リスク) < 0.95 (通常の早期リタイア期係数) なのでこちらが優先
    assert result.safe_monthly == round(20.0 * 0.85, 2)


def test_sequence_risk_factor_ignored_when_less_strict_than_stage_factor():
    result = calculate_monthly_budget(
        fire_result=_healthy_fire_result(),
        action_result=_healthy_action_result(),
        current_age=62,
        pension_start_age=70,
        sequence_risk_factor=0.99,
    )

    assert "sequence_risk_evaluated" in result.reasons
    assert "sequence_risk_applied" not in result.reasons
    # 通常の早期リタイア期係数0.95の方が厳しいので、そちらを維持
    assert result.safe_monthly == round(20.0 * 0.95, 2)


def test_more_severe_existing_factor_still_wins_over_sequence_risk():
    # 市場暴落中は既存係数(0.60)の方が系列リスク係数(0.85)より厳しい
    result = calculate_monthly_budget(
        fire_result=_healthy_fire_result(),
        action_result=_healthy_action_result(),
        market_crash=True,
        current_age=62,
        pension_start_age=70,
        sequence_risk_factor=0.85,
    )

    assert result.safe_monthly == round(20.0 * 0.60, 2)


def test_none_sequence_risk_factor_behaves_like_before():
    result = calculate_monthly_budget(
        fire_result=_healthy_fire_result(),
        action_result=_healthy_action_result(),
        current_age=62,
        pension_start_age=70,
        sequence_risk_factor=None,
    )

    assert "sequence_risk_evaluated" not in result.reasons
    assert result.safe_monthly == round(20.0 * 0.95, 2)


def test_max_monthly_and_status_unaffected_by_sequence_risk_factor():
    result = calculate_monthly_budget(
        fire_result=_healthy_fire_result(),
        action_result=_healthy_action_result(),
        current_age=62,
        pension_start_age=70,
        sequence_risk_factor=0.80,
    )

    assert result.status == "green"
    assert result.max_monthly == round(20.0 * 1.15, 2)
