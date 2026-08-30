import pytest

from services.large_expense_engine import (
    add_large_expense,
    distribution_end_month,
    expenses_for_month,
    load_large_expenses,
    total_for_month,
)


@pytest.fixture
def expense_path(tmp_path):
    return tmp_path / "expenses.json"


# --- 後方互換（distribution_months省略・1件の従来通り単月計上） ---

def test_add_large_expense_default_distribution_is_one(expense_path):
    record = add_large_expense(
        "沖縄旅行",
        "旅行",
        30.0,
        "2026-09",
        path=expense_path,
    )
    assert record["distribution_months"] == 1


def test_total_for_month_backward_compatible_single_month(expense_path):
    add_large_expense("沖縄旅行", "旅行", 30.0, "2026-09", path=expense_path)

    expenses = load_large_expenses(path=expense_path)

    assert total_for_month(expenses, "2026-09") == 30.0
    assert total_for_month(expenses, "2026-10") == 0.0


def test_legacy_record_without_distribution_months_key_treated_as_one(expense_path):
    # distribution_monthsキーを持たない旧データを模擬する
    expense_path.write_text(
        '[{"id": "abc", "name": "車検", "category": "車", "amount": 12.0, '
        '"expected_month": "2026-11", "memo": "", "created_at": "2026-01-01T00:00:00+00:00"}]',
        encoding="utf-8",
    )

    expenses = load_large_expenses(path=expense_path)

    assert total_for_month(expenses, "2026-11") == 12.0
    assert total_for_month(expenses, "2026-12") == 0.0


# --- 複数月分散（Sprint 26） ---

def test_even_split_across_months(expense_path):
    add_large_expense(
        "沖縄旅行",
        "旅行",
        90.0,
        "2026-09",
        distribution_months=3,
        path=expense_path,
    )

    expenses = load_large_expenses(path=expense_path)

    assert total_for_month(expenses, "2026-09") == 30.0
    assert total_for_month(expenses, "2026-10") == 30.0
    assert total_for_month(expenses, "2026-11") == 30.0
    assert total_for_month(expenses, "2026-12") == 0.0


def test_remainder_distributed_across_months_not_lumped_into_last(expense_path):
    # 100 / 3 = 33.33... → 33.34 + 33.33 + 33.33 のように端数を前方の月から分散する
    add_large_expense(
        "医療費",
        "医療",
        100.0,
        "2026-01",
        distribution_months=3,
        path=expense_path,
    )

    expenses = load_large_expenses(path=expense_path)

    jan = total_for_month(expenses, "2026-01")
    feb = total_for_month(expenses, "2026-02")
    mar = total_for_month(expenses, "2026-03")

    # 端数(1銭)は最初の月に寄る想定だが、実装詳細ではなく「合計が一致」
    # 「差が0.01万円以内」であることを検証する
    assert round(jan + feb + mar, 2) == 100.0
    assert round(max(jan, feb, mar) - min(jan, feb, mar), 2) <= 0.01


def test_distribution_across_year_boundary(expense_path):
    add_large_expense(
        "車",
        "車",
        60.0,
        "2026-11",
        distribution_months=4,
        path=expense_path,
    )

    expenses = load_large_expenses(path=expense_path)

    assert total_for_month(expenses, "2026-11") == 15.0
    assert total_for_month(expenses, "2026-12") == 15.0
    assert total_for_month(expenses, "2027-01") == 15.0
    assert total_for_month(expenses, "2027-02") == 15.0
    assert total_for_month(expenses, "2027-03") == 0.0


def test_multiple_expenses_summed_in_same_month(expense_path):
    add_large_expense(
        "沖縄旅行", "旅行", 90.0, "2026-09", distribution_months=3, path=expense_path
    )
    add_large_expense("車検", "車", 12.0, "2026-10", path=expense_path)

    expenses = load_large_expenses(path=expense_path)

    # 9月分割(30) + 10月分割(30) + 車検(12) = 42
    assert total_for_month(expenses, "2026-10") == 42.0


def test_expenses_for_month_returns_amount_for_month(expense_path):
    add_large_expense(
        "沖縄旅行", "旅行", 90.0, "2026-09", distribution_months=3, path=expense_path
    )

    expenses = load_large_expenses(path=expense_path)
    october_entries = expenses_for_month(expenses, "2026-10")

    assert len(october_entries) == 1
    assert october_entries[0]["amount_for_month"] == 30.0
    assert october_entries[0]["amount"] == 90.0  # 元の合計額は変更しない


def test_distribution_end_month(expense_path):
    record = add_large_expense(
        "沖縄旅行", "旅行", 90.0, "2026-11", distribution_months=3, path=expense_path
    )
    assert distribution_end_month(record) == "2027-01"


def test_distribution_end_month_single_month_unchanged(expense_path):
    record = add_large_expense(
        "車検", "車", 12.0, "2026-10", path=expense_path
    )
    assert distribution_end_month(record) == "2026-10"


# --- バリデーション ---

def test_distribution_months_must_be_positive_int(expense_path):
    with pytest.raises(ValueError):
        add_large_expense(
            "旅行", "旅行", 30.0, "2026-09", distribution_months=0, path=expense_path
        )


def test_distribution_months_must_be_int_not_float(expense_path):
    with pytest.raises(ValueError):
        add_large_expense(
            "旅行", "旅行", 30.0, "2026-09", distribution_months=2.5, path=expense_path
        )
