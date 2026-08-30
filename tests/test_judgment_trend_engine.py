import pytest

from services.judgment_trend_engine import (
    load_judgment_trend,
    record_monthly_judgment,
)


@pytest.fixture
def trend_path(tmp_path):
    return tmp_path / "trend.json"


def test_record_and_load_single_month(trend_path):
    record_monthly_judgment(
        "2026-08",
        safe_monthly=30.0,
        recommended_monthly=32.0,
        max_monthly=36.0,
        status="green",
        binding_safe_factor_reason="cash_buffer_healthy",
        path=trend_path,
    )

    records = load_judgment_trend(path=trend_path)

    assert len(records) == 1
    assert records[0]["month"] == "2026-08"
    assert records[0]["safe_monthly"] == 30.0
    assert records[0]["status"] == "green"


def test_same_month_overwrites_previous_record(trend_path):
    record_monthly_judgment(
        "2026-08", 30.0, 32.0, 36.0, "green", path=trend_path
    )
    record_monthly_judgment(
        "2026-08", 25.0, 32.0, 36.0, "yellow", path=trend_path
    )

    records = load_judgment_trend(path=trend_path)

    assert len(records) == 1
    assert records[0]["safe_monthly"] == 25.0
    assert records[0]["status"] == "yellow"


def test_different_months_accumulate_and_sort_ascending(trend_path):
    record_monthly_judgment("2026-09", 31.0, 33.0, 37.0, "green", path=trend_path)
    record_monthly_judgment("2026-07", 29.0, 31.0, 35.0, "red", path=trend_path)
    record_monthly_judgment("2026-08", 30.0, 32.0, 36.0, "yellow", path=trend_path)

    records = load_judgment_trend(path=trend_path)

    assert [r["month"] for r in records] == ["2026-07", "2026-08", "2026-09"]


def test_invalid_month_format_raises(trend_path):
    with pytest.raises(ValueError):
        record_monthly_judgment("2026/08", 30.0, 32.0, 36.0, "green", path=trend_path)


def test_invalid_status_raises(trend_path):
    with pytest.raises(ValueError):
        record_monthly_judgment(
            "2026-08", 30.0, 32.0, 36.0, "blue", path=trend_path
        )


def test_negative_amount_raises(trend_path):
    with pytest.raises(ValueError):
        record_monthly_judgment(
            "2026-08", -1.0, 32.0, 36.0, "green", path=trend_path
        )


def test_load_returns_empty_list_when_file_missing(trend_path):
    assert load_judgment_trend(path=trend_path) == []
