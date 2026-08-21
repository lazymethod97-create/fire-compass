from services.report_generator import build_report_html, report_filename


def _record():
    return {
        "name": "FIRE <テスト>",
        "created_at": "2026-08-21T12:00:00+00:00",
        "inputs": {
            "current_age": 43,
            "current_assets": 4700,
            "market_condition": "通常",
        },
        "results": {
            "asset_depletion_label": "余裕あり",
            "recommended_monthly_spending": 12.3,
            "cash_months": 58.5,
            "recommended_action": "追加投資",
            "additional_investment": 100.0,
            "investment_withdrawal": 0.0,
            "pension_gap_after_start": 50.0,
            "nisa_remaining_limit": 1200.0,
            "nisa_growth_remaining_limit": 1000.0,
            "nisa_annual_room": 260.0,
            "ideco_annual_contribution": 12.0,
        },
        "scenarios": [
            {
                "name": "標準ケース",
                "final_assets": 5000.0,
                "min_assets": 3000.0,
                "depleted_at": "期間内に枯渇せず",
            }
        ],
    }


def test_build_report_contains_core_information():
    html = build_report_html(_record())

    assert "FIRE Compass レポート" in html
    assert "余裕あり" in html
    assert "12.3万円" in html
    assert "標準ケース" in html
    assert "NISA残り総枠" in html
    assert "金融商品の売買や特定の投資行動を断定するものではなく" in html


def test_report_escapes_html_input():
    html = build_report_html(_record())

    assert "<テスト>" not in html
    assert "&lt;テスト&gt;" in html


def test_report_filename_is_safe():
    filename = report_filename({"name": "8月 / FIRE:テスト?"})

    assert filename.endswith("_report.html")
    assert "/" not in filename
    assert ":" not in filename
    assert "?" not in filename
