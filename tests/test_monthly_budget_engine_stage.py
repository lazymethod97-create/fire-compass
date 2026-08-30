import pytest

from services.action_engine import ActionResult
from services.fire_engine import FireResult, ScenarioSummary
from services.monthly_budget_engine import calculate_monthly_budget


def _healthy_fire_result(recommended_monthly=20.0):
    return FireResult(
        net_annual_spending=240.0,
        recommended_monthly_spending=recommended_monthly,
        cash_months=18.0,
        asset_depletion_label="余裕あり",
        advice="",
        yearly_df=None,
        scenario_summaries=[
            ScenarioSummary(
                name="標準ケース",
                final_assets=5000.0,
                min_assets=3000.0,
                depleted_at="期間内に枯渇せず",
            ),
            ScenarioSummary(
                name="悲観ケース",
                final_assets=1000.0,
                min_assets=500.0,
                depleted_at="期間内に枯渇せず",
            ),
            ScenarioSummary(
                name="楽観ケース",
                final_assets=8000.0,
                min_assets=6000.0,
                depleted_at="期間内に枯渇せず",
            ),
        ],
    )


def _healthy_action_result():
    return ActionResult(
        target_cash_amount=240.0,
        target_cash_months=12.0,
        cash_surplus=100.0,
        cash_shortage=0.0,
        additional_investment=100.0,
        investment_withdrawal=0.0,
        action="追加投資",
        reason="",
    )


def _crash_action_result():
    return ActionResult(
        target_cash_amount=240.0,
        target_cash_months=12.0,
        cash_surplus=0.0,
        cash_shortage=0.0,
        additional_investment=0.0,
        investment_withdrawal=0.0,
        action="取り崩し・追加投資は不要",
        reason="",
    )


class TestBackwardCompatibility:
    def test_no_stage_args_unchanged(self):
        """current_age/pension_start_ageを渡さない既存呼び出しは、
        Sprint 20までと同じ結果になる。"""
        result = calculate_monthly_budget(
            fire_result=_healthy_fire_result(),
            action_result=_healthy_action_result(),
        )
        assert result.safe_monthly == 20.0
        assert "early_retirement_stage" not in result.reasons
        assert "late_stage_conservative" not in result.reasons

    def test_current_age_only_no_adjustment(self):
        """pension_start_ageが未指定なら、current_ageだけではステージ調整しない。"""
        result = calculate_monthly_budget(
            fire_result=_healthy_fire_result(),
            action_result=_healthy_action_result(),
            current_age=62,
        )
        assert result.safe_monthly == 20.0
        assert "early_retirement_stage" not in result.reasons


class TestStageClassification:
    def test_pre_60_no_adjustment(self):
        result = calculate_monthly_budget(
            fire_result=_healthy_fire_result(),
            action_result=_healthy_action_result(),
            current_age=55,
            pension_start_age=65,
        )
        assert result.safe_monthly == 20.0
        assert "early_retirement_stage" not in result.reasons
        assert "late_stage_conservative" not in result.reasons

    def test_early_retirement_stage_lowers_safe_monthly(self):
        result = calculate_monthly_budget(
            fire_result=_healthy_fire_result(),
            action_result=_healthy_action_result(),
            current_age=62,
            pension_start_age=65,
        )
        assert "early_retirement_stage" in result.reasons
        assert result.safe_monthly == 19.0  # 20.0 * 0.95

    def test_receiving_pension_stage_no_extra_adjustment(self):
        """年金受給開始年齢〜74歳は既存ロジックのみ（追加係数なし）。"""
        result = calculate_monthly_budget(
            fire_result=_healthy_fire_result(),
            action_result=_healthy_action_result(),
            current_age=68,
            pension_start_age=65,
        )
        assert "early_retirement_stage" not in result.reasons
        assert "late_stage_conservative" not in result.reasons
        assert result.safe_monthly == 20.0

    def test_late_stage_lowers_safe_monthly(self):
        result = calculate_monthly_budget(
            fire_result=_healthy_fire_result(),
            action_result=_healthy_action_result(),
            current_age=80,
            pension_start_age=65,
        )
        assert "late_stage_conservative" in result.reasons
        assert result.safe_monthly == 18.0  # 20.0 * 0.90

    def test_pension_start_age_boundary_is_early_retirement_end(self):
        """年金受給開始年齢ちょうどの場合はreceiving_pension（早期リタイアではない）。"""
        result = calculate_monthly_budget(
            fire_result=_healthy_fire_result(),
            action_result=_healthy_action_result(),
            current_age=65,
            pension_start_age=65,
        )
        assert "early_retirement_stage" not in result.reasons
        assert result.safe_monthly == 20.0

    def test_late_stage_boundary_at_75(self):
        result = calculate_monthly_budget(
            fire_result=_healthy_fire_result(),
            action_result=_healthy_action_result(),
            current_age=75,
            pension_start_age=65,
        )
        assert "late_stage_conservative" in result.reasons


class TestStageDoesNotOverrideMoreConservativeFactor:
    def test_market_crash_factor_is_more_conservative_than_stage(self):
        """市場暴落時（係数0.60）は、早期リタイア期の係数0.95より厳しいため、
        ステージ係数で上書きされない。"""
        result = calculate_monthly_budget(
            fire_result=_healthy_fire_result(),
            action_result=_crash_action_result(),
            market_crash=True,
            current_age=62,
            pension_start_age=65,
        )
        assert "early_retirement_stage" in result.reasons
        assert "market_crash_active" in result.reasons
        assert result.safe_monthly == 12.0  # 20.0 * 0.60（暴落係数が優先）

    def test_market_crash_factor_is_more_conservative_than_late_stage(self):
        result = calculate_monthly_budget(
            fire_result=_healthy_fire_result(),
            action_result=_crash_action_result(),
            market_crash=True,
            current_age=80,
            pension_start_age=65,
        )
        assert "late_stage_conservative" in result.reasons
        assert result.safe_monthly == 12.0  # 20.0 * 0.60（暴落係数が優先）


class TestStageDoesNotAffectMaxOrStatus:
    def test_late_stage_does_not_change_max_monthly_or_status(self):
        """今回のSprintは安全生活費の係数調整のみが対象。
        上限生活費・ガードレール判定（green/yellow/red）はステージで変化しない。"""
        result = calculate_monthly_budget(
            fire_result=_healthy_fire_result(),
            action_result=_healthy_action_result(),
            current_age=80,
            pension_start_age=65,
        )
        assert result.max_monthly == 23.0  # 20.0 * 1.15（変化なし）
        assert result.status == "green"


class TestValidation:
    def test_negative_current_age_raises(self):
        with pytest.raises(ValueError):
            calculate_monthly_budget(
                fire_result=_healthy_fire_result(),
                action_result=_healthy_action_result(),
                current_age=-1,
                pension_start_age=65,
            )

    def test_negative_pension_start_age_raises(self):
        with pytest.raises(ValueError):
            calculate_monthly_budget(
                fire_result=_healthy_fire_result(),
                action_result=_healthy_action_result(),
                current_age=62,
                pension_start_age=-1,
            )
