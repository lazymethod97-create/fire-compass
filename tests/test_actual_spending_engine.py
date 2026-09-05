import json

import pytest

from services.actual_spending_engine import (
    build_spending_comparison,
    delete_actual_spending,
    load_actual_spending,
    record_actual_spending,
)


@pytest.fixture
def spending_path(tmp_path):
    return tmp_path / "actual_spending.json"


def test_record_and_load_roundtrip(spending_path):
    record_actual_spending("2026-01", 11.5, memo="正月出費", path=spending_path)
    records = load_actual_spending(path=spending_path)

    assert len(records) == 1
    assert records[0]["month"] == "2026-01"
    assert records[0]["actual_amount"] == 11.5
    assert records[0]["memo"] == "正月出費"


def test_same_month_is_overwritten_not_duplicated(spending_path):
    record_actual_spending("2026-01", 11.5, path=spending_path)
    record_actual_spending("2026-01", 13.0, path=spending_path)

    records = load_actual_spending(path=spending_path)

    assert len(records) == 1
    assert records[0]["actual_amount"] == 13.0


def test_records_are_sorted_by_month(spending_path):
    record_actual_spending("2026-03", 10.0, path=spending_path)
    record_actual_spending("2026-01", 11.0, path=spending_path)
    record_actual_spending("2026-02", 9.0, path=spending_path)

    records = load_actual_spending(path=spending_path)

    assert [r["month"] for r in records] == ["2026-01", "2026-02", "2026-03"]


def test_delete_removes_only_target_month(spending_path):
    record_actual_spending("2026-01", 11.0, path=spending_path)
    record_actual_spending("2026-02", 9.0, path=spending_path)

    deleted = delete_actual_spending("2026-01", path=spending_path)

    assert deleted is True
    remaining = load_actual_spending(path=spending_path)
    assert [r["month"] for r in remaining] == ["2026-02"]


def test_delete_returns_false_when_month_not_found(spending_path):
    record_actual_spending("2026-01", 11.0, path=spending_path)

    assert delete_actual_spending("2026-12", path=spending_path) is False


@pytest.mark.parametrize(
    "month,amount",
    [("2026-13", 10.0), ("not-a-month", 10.0), ("2026-01", -1.0)],
)
def test_invalid_inputs_raise_value_error(spending_path, month, amount):
    with pytest.raises(ValueError):
        record_actual_spending(month, amount, path=spending_path)


def test_corrupted_file_returns_empty_list(spending_path):
    spending_path.write_text("not valid json", encoding="utf-8")
    assert load_actual_spending(path=spending_path) == []


def test_comparison_matches_month_with_both_records_present():
    actual_records = [{"month": "2026-01", "actual_amount": 12.0}]
    judgment_records = [
        {
            "month": "2026-01",
            "safe_monthly": 8.61,
            "recommended_monthly": 12.3,
            "max_monthly": 12.3,
            "status": "red",
        }
    ]

    rows = build_spending_comparison(actual_records, judgment_records)

    assert len(rows) == 1
    row = rows[0]
    assert row.month == "2026-01"
    assert row.variance_vs_recommended == round(12.0 - 12.3, 2)
    assert row.within_safe_to_max_range is True


def test_comparison_keeps_months_with_only_one_side_present():
    actual_records = [{"month": "2026-02", "actual_amount": 9.0}]
    judgment_records = [
        {
            "month": "2026-03",
            "safe_monthly": 10.0,
            "recommended_monthly": 12.0,
            "max_monthly": 14.0,
            "status": "green",
        }
    ]

    rows = build_spending_comparison(actual_records, judgment_records)
    rows_by_month = {row.month: row for row in rows}

    assert rows_by_month["2026-02"].safe_monthly is None
    assert rows_by_month["2026-02"].variance_vs_recommended is None
    assert rows_by_month["2026-03"].actual_amount is None
    assert rows_by_month["2026-03"].within_safe_to_max_range is None


def test_comparison_detects_overspending_and_underspending():
    judgment_records = [
        {
            "month": "2026-01",
            "safe_monthly": 8.0,
            "recommended_monthly": 10.0,
            "max_monthly": 12.0,
            "status": "green",
        }
    ]

    over = build_spending_comparison(
        [{"month": "2026-01", "actual_amount": 15.0}], judgment_records
    )[0]
    under = build_spending_comparison(
        [{"month": "2026-01", "actual_amount": 5.0}], judgment_records
    )[0]
    within = build_spending_comparison(
        [{"month": "2026-01", "actual_amount": 9.0}], judgment_records
    )[0]

    assert over.within_safe_to_max_range is False
    assert over.variance_vs_recommended == 5.0
    assert under.within_safe_to_max_range is False
    assert under.variance_vs_recommended == -5.0
    assert within.within_safe_to_max_range is True


def test_comparison_rejects_non_list_inputs():
    with pytest.raises(ValueError):
        build_spending_comparison({}, [])
    with pytest.raises(ValueError):
        build_spending_comparison([], {})
