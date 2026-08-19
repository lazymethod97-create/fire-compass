from types import SimpleNamespace

from services.ai_advisor import generate_ai_advice


def _make_inputs():
    fire_result = SimpleNamespace(
        net_annual_spending=164.0,
        recommended_monthly_spending=12.3,
        cash_months=58.5,
        asset_depletion_label="余裕あり",
        advice="標準ケースでは資産を維持または増加させながら生活できる計算です。",
        scenario_summaries=[
            SimpleNamespace(
                name="標準ケース",
                final_assets=5000.0,
                min_assets=3000.0,
                depleted_at="期間内に枯渇せず",
            ),
            SimpleNamespace(
                name="悲観ケース",
                final_assets=2500.0,
                min_assets=1000.0,
                depleted_at="期間内に枯渇せず",
            ),
            SimpleNamespace(
                name="楽観ケース",
                final_assets=7000.0,
                min_assets=4000.0,
                depleted_at="期間内に枯渇せず",
            ),
        ],
    )

    strategy = SimpleNamespace(
        target_cash_months=12.0,
        additional_investment_ratio=1.0,
        spending_reduction_pct=0.0,
        recommended_monthly_spending=12.3,
        reason="通常時なので、Sprint 2の通常ルールをそのまま使用します。",
    )

    return fire_result, strategy


def test_fallback_when_api_key_is_missing(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    fire_result, strategy = _make_inputs()

    result = generate_ai_advice(
        fire_result=fire_result,
        market_condition="通常",
        strategy=strategy,
        recommended_action="追加投資",
        additional_investment=100.0,
        investment_withdrawal=0.0,
    )

    assert "AI FIREアドバイス" in result
    assert "通常" in result
    assert "追加投資" in result


def test_fallback_contains_core_financial_information(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    fire_result, strategy = _make_inputs()

    result = generate_ai_advice(
        fire_result=fire_result,
        market_condition="暴落",
        strategy=strategy,
        recommended_action="投資資産から現金を補充",
        additional_investment=0.0,
        investment_withdrawal=50.0,
    )

    assert "164" in result
    assert "投資資産から現金を補充" in result
    assert "目標現金" in result