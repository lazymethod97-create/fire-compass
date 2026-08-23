import pytest

from services.comparison_engine import build_comparison


def _record(name, cash_months, additional_investment=0.0, action="追加投資"):
    return {
        "name": name,
        "created_at": "2026-08-21T12:00:00+00:00",
        "results": {
            "asset_depletion_label": "余裕あり",
            "net_annual_spending": 180.0,
            "recommended_monthly_spending": 13.5,
            "cash_months": cash_months,
            "target_cash": 180.0,
            "additional_investment": additional_investment,
            "investment_withdrawal": 0.0,
            "recommended_action": action,
            "pension_gap_after_start": 20.0,
            "nisa_remaining_limit": 1200.0,
            "nisa_growth_remaining_limit": 900.0,
            "nisa_annual_room": 200.0,
            "ideco_annual_contribution": 12.0,
        },
    }


def test_build_comparison_returns_names_and_rows():
    result = build_comparison([_record("A", 24.0), _record("B", 36.0)])

    assert result.names == ["A", "B"]
    assert result.created_ats == [
        "2026-08-21T12:00:00+00:00",
        "2026-08-21T12:00:00+00:00",
    ]
    assert len(result.rows) > 0


def test_build_comparison_computes_diff_against_first_record():
    result = build_comparison([_record("A", 24.0), _record("B", 36.0)])

    cash_row = next(row for row in result.rows if row.key == "cash_months")
    assert cash_row.values == [24.0, 36.0]
    assert cash_row.diffs == [0.0, 12.0]


def test_build_comparison_handles_non_numeric_fields():
    result = build_comparison(
        [
            _record("A", 24.0, action="追加投資"),
            _record("B", 36.0, action="取り崩し・追加投資は不要"),
        ]
    )

    action_row = next(
        row for row in result.rows if row.key == "recommended_action"
    )
    assert action_row.values == ["追加投資", "取り崩し・追加投資は不要"]
    assert action_row.diffs == [None, None]


def test_build_comparison_handles_missing_results_key():
    record_without_results = {"name": "C", "created_at": "不明"}

    result = build_comparison([_record("A", 24.0), record_without_results])

    cash_row = next(row for row in result.rows if row.key == "cash_months")
    assert cash_row.values == [24.0, None]
    assert cash_row.diffs == [0.0, None]


def test_build_comparison_supports_up_to_four_records():
    records = [_record(f"case{i}", 20.0 + i) for i in range(4)]

    result = build_comparison(records)

    assert len(result.names) == 4


def test_build_comparison_requires_at_least_two_records():
    with pytest.raises(ValueError):
        build_comparison([_record("A", 24.0)])


def test_build_comparison_rejects_more_than_four_records():
    records = [_record(f"case{i}", 20.0 + i) for i in range(5)]

    with pytest.raises(ValueError):
        build_comparison(records)


def test_build_comparison_rejects_non_dict_records():
    with pytest.raises(ValueError):
        build_comparison([_record("A", 24.0), "not-a-dict"])


def test_build_comparison_rejects_non_list_input():
    with pytest.raises(ValueError):
        build_comparison({"A": _record("A", 24.0)})
