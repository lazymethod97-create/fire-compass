from services.budget_explanation import build_budget_explanation


def test_healthy_case_has_no_binding_factor_message():
    explanation = build_budget_explanation(
        ["cash_buffer_healthy", "upside_allowed"],
        "cash_buffer_healthy",
    )

    assert "ありません" in explanation.binding_summary
    assert len(explanation.details) == 2


def test_market_crash_is_labeled_as_binding_factor():
    explanation = build_budget_explanation(
        ["market_crash_active"],
        "market_crash_active",
    )

    assert "市場の暴落局面" in explanation.binding_summary
    assert any("60%" in d for d in explanation.details)


def test_bear_case_depletes_message():
    explanation = build_budget_explanation(
        ["bear_case_depletes"],
        "bear_case_depletes",
    )

    assert "資産寿命シミュレーションの悲観ケース" in explanation.binding_summary
    assert any("70%" in d for d in explanation.details)


def test_cash_buffer_below_target_message():
    explanation = build_budget_explanation(
        ["cash_buffer_below_target"],
        "cash_buffer_below_target",
    )

    assert "現金バッファ不足" in explanation.binding_summary
    assert any("85%" in d for d in explanation.details)


def test_early_retirement_stage_message():
    explanation = build_budget_explanation(
        ["early_retirement_stage"],
        "early_retirement_stage",
    )

    assert "早期リタイア期の調整" in explanation.binding_summary
    assert any("95%" in d for d in explanation.details)


def test_late_stage_message():
    explanation = build_budget_explanation(
        ["late_stage_conservative"],
        "late_stage_conservative",
    )

    assert "75歳以降の保守的な調整" in explanation.binding_summary
    assert any("90%" in d for d in explanation.details)


def test_sequence_risk_applied_suppresses_evaluated_duplicate():
    explanation = build_budget_explanation(
        ["early_retirement_stage", "sequence_risk_evaluated", "sequence_risk_applied"],
        "sequence_risk_applied",
    )

    evaluated_count = sum(
        1 for d in explanation.details if "評価しましたが" in d
    )
    applied_count = sum(1 for d in explanation.details if "評価した結果" in d)

    assert evaluated_count == 0
    assert applied_count == 1
    assert "シーケンス・オブ・リターンズ・リスク" in explanation.binding_summary


def test_sequence_risk_evaluated_without_applied_is_shown():
    explanation = build_budget_explanation(
        ["early_retirement_stage", "sequence_risk_evaluated"],
        "early_retirement_stage",
    )

    assert any("評価しましたが" in d for d in explanation.details)
    assert "早期リタイア期の調整" in explanation.binding_summary


def test_large_expense_messages_both_variants():
    exceeds = build_budget_explanation(
        ["cash_buffer_healthy", "large_expense_exceeds_cash_surplus"],
        "cash_buffer_healthy",
    )
    within = build_budget_explanation(
        ["cash_buffer_healthy", "large_expense_within_cash_surplus"],
        "cash_buffer_healthy",
    )

    assert any("超える" in d for d in exceeds.details)
    assert any("範囲内" in d for d in within.details)


def test_display_order_is_stable_regardless_of_input_order():
    explanation_a = build_budget_explanation(
        ["upside_allowed", "cash_buffer_healthy"],
        "cash_buffer_healthy",
    )
    explanation_b = build_budget_explanation(
        ["cash_buffer_healthy", "upside_allowed"],
        "cash_buffer_healthy",
    )

    assert explanation_a.details == explanation_b.details


def test_unknown_binding_reason_falls_back_gracefully():
    explanation = build_budget_explanation(
        ["cash_buffer_healthy"],
        "some_future_unmapped_reason",
    )

    assert "通常のルール" in explanation.binding_summary


def test_unknown_reason_tag_is_ignored():
    explanation = build_budget_explanation(
        ["cash_buffer_healthy", "some_future_unmapped_tag"],
        "cash_buffer_healthy",
    )

    assert len(explanation.details) == 1


def test_empty_reasons_returns_empty_details():
    explanation = build_budget_explanation([], "cash_buffer_healthy")

    assert explanation.details == []
    assert "ありません" in explanation.binding_summary
