import pytest

from services.large_expense_engine import (
    add_large_expense,
    delete_large_expense,
    expenses_for_month,
    load_large_expenses,
    total_for_month,
)


@pytest.fixture
def expense_path(tmp_path):
    return tmp_path / ".fire_compass_large_expenses.json"


def test_add_large_expense_persists_and_returns_record(expense_path):
    record = add_large_expense(
        "沖縄旅行",
        "旅行",
        30.0,
        "2026-10",
        memo="家族旅行",
        path=expense_path,
    )

    assert record["name"] == "沖縄旅行"
    assert record["category"] == "旅行"
    assert record["amount"] == 30.0
    assert record["expected_month"] == "2026-10"
    assert record["memo"] == "家族旅行"
    assert record["id"]
    assert record["created_at"]

    loaded = load_large_expenses(path=expense_path)
    assert len(loaded) == 1
    assert loaded[0]["id"] == record["id"]


def test_add_large_expense_trims_name_and_memo(expense_path):
    record = add_large_expense(
        "  車検  ",
        "車",
        15.0,
        "2026-11",
        memo="  ディーラーで実施  ",
        path=expense_path,
    )
    assert record["name"] == "車検"
    assert record["memo"] == "ディーラーで実施"


@pytest.mark.parametrize(
    "name,category,amount,month",
    [
        ("", "旅行", 10.0, "2026-10"),
        ("   ", "旅行", 10.0, "2026-10"),
        ("旅行", "レジャー", 10.0, "2026-10"),
        ("旅行", "旅行", -1.0, "2026-10"),
        ("旅行", "旅行", 10.0, "2026/10"),
        ("旅行", "旅行", 10.0, "26-10"),
        ("旅行", "旅行", 10.0, ""),
    ],
)
def test_add_large_expense_validation_errors(expense_path, name, category, amount, month):
    with pytest.raises(ValueError):
        add_large_expense(name, category, amount, month, path=expense_path)


def test_load_large_expenses_sorted_by_month_then_created_at(expense_path):
    add_large_expense("車検", "車", 15.0, "2027-01", path=expense_path)
    add_large_expense("旅行A", "旅行", 20.0, "2026-10", path=expense_path)
    add_large_expense("旅行B", "旅行", 5.0, "2026-10", path=expense_path)

    loaded = load_large_expenses(path=expense_path)
    months = [item["expected_month"] for item in loaded]
    assert months == ["2026-10", "2026-10", "2027-01"]
    assert [item["name"] for item in loaded if item["expected_month"] == "2026-10"] == [
        "旅行A",
        "旅行B",
    ]


def test_load_large_expenses_missing_file_returns_empty_list(expense_path):
    assert load_large_expenses(path=expense_path) == []


def test_delete_large_expense_removes_matching_record(expense_path):
    record = add_large_expense("車検", "車", 15.0, "2026-11", path=expense_path)
    add_large_expense("旅行", "旅行", 20.0, "2026-10", path=expense_path)

    deleted = delete_large_expense(record["id"], path=expense_path)
    assert deleted is True

    remaining = load_large_expenses(path=expense_path)
    assert len(remaining) == 1
    assert remaining[0]["name"] == "旅行"


def test_delete_large_expense_returns_false_when_not_found(expense_path):
    add_large_expense("旅行", "旅行", 20.0, "2026-10", path=expense_path)
    assert delete_large_expense("does-not-exist", path=expense_path) is False


def test_delete_large_expense_requires_id(expense_path):
    with pytest.raises(ValueError):
        delete_large_expense("", path=expense_path)


def test_total_for_month_sums_matching_records_only():
    expenses = [
        {"expected_month": "2026-10", "amount": 30.0},
        {"expected_month": "2026-10", "amount": 12.5},
        {"expected_month": "2026-11", "amount": 100.0},
    ]
    assert total_for_month(expenses, "2026-10") == 42.5
    assert total_for_month(expenses, "2026-11") == 100.0
    assert total_for_month(expenses, "2026-12") == 0.0


def test_total_for_month_ignores_non_dict_items():
    expenses = [{"expected_month": "2026-10", "amount": 10.0}, "not-a-dict"]
    assert total_for_month(expenses, "2026-10") == 10.0


def test_total_for_month_rejects_non_list():
    with pytest.raises(ValueError):
        total_for_month("not-a-list", "2026-10")


def test_expenses_for_month_filters_correctly():
    expenses = [
        {"expected_month": "2026-10", "name": "旅行A"},
        {"expected_month": "2026-11", "name": "車検"},
    ]
    result = expenses_for_month(expenses, "2026-10")
    assert len(result) == 1
    assert result[0]["name"] == "旅行A"


def test_expenses_for_month_rejects_non_list():
    with pytest.raises(ValueError):
        expenses_for_month("not-a-list", "2026-10")
