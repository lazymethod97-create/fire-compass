import pytest

from services.history_manager import (
    clear_history,
    delete_history,
    export_history_to_csv,
    filter_history,
    history_export_filename,
    load_history,
    rename_history,
    save_history,
)


def test_save_and_load_history(tmp_path):
    history_path = tmp_path / "history.json"

    record = save_history(
        {
            "name": "テストFIRE",
            "assets": 4700,
        },
        path=history_path,
    )

    history = load_history(path=history_path)

    assert len(history) == 1
    assert history[0]["id"] == record["id"]
    assert history[0]["name"] == "テストFIRE"
    assert history[0]["assets"] == 4700
    assert "created_at" in history[0]


def test_history_is_newest_first(tmp_path):
    history_path = tmp_path / "history.json"

    save_history(
        {"name": "旧"},
        path=history_path,
    )

    save_history(
        {"name": "新"},
        path=history_path,
    )

    history = load_history(path=history_path)

    assert len(history) == 2
    assert history[0]["name"] == "新"


def test_history_is_limited_to_20_records(tmp_path):
    history_path = tmp_path / "history.json"

    for number in range(25):
        save_history(
            {"name": f"履歴{number}"},
            path=history_path,
        )

    history = load_history(path=history_path)

    assert len(history) == 20
    assert history[0]["name"] == "履歴24"


def test_delete_history(tmp_path):
    history_path = tmp_path / "history.json"

    record = save_history(
        {"name": "削除対象"},
        path=history_path,
    )

    assert delete_history(
        record["id"],
        path=history_path,
    ) is True

    assert load_history(
        path=history_path,
    ) == []


def test_rename_history(tmp_path):
    history_path = tmp_path / "history.json"

    record = save_history(
        {"name": "変更前", "assets": 1000},
        path=history_path,
    )

    assert rename_history(
        record["id"],
        "変更後",
        path=history_path,
    ) is True

    history = load_history(path=history_path)

    assert len(history) == 1
    assert history[0]["name"] == "変更後"
    # 名称以外のフィールドは変更されない。
    assert history[0]["assets"] == 1000
    assert history[0]["id"] == record["id"]


def test_rename_history_trims_whitespace(tmp_path):
    history_path = tmp_path / "history.json"

    record = save_history(
        {"name": "元の名前"},
        path=history_path,
    )

    rename_history(
        record["id"],
        "  前後に空白  ",
        path=history_path,
    )

    history = load_history(path=history_path)

    assert history[0]["name"] == "前後に空白"


def test_rename_history_missing_id_returns_false(tmp_path):
    history_path = tmp_path / "history.json"

    save_history(
        {"name": "既存"},
        path=history_path,
    )

    assert rename_history(
        "存在しないID",
        "新しい名前",
        path=history_path,
    ) is False


def test_rename_history_requires_history_id(tmp_path):
    history_path = tmp_path / "history.json"

    with pytest.raises(ValueError):
        rename_history(
            "",
            "新しい名前",
            path=history_path,
        )


def test_rename_history_requires_non_empty_name(tmp_path):
    history_path = tmp_path / "history.json"

    record = save_history(
        {"name": "既存"},
        path=history_path,
    )

    with pytest.raises(ValueError):
        rename_history(
            record["id"],
            "   ",
            path=history_path,
        )


def _named_records():
    return [
        {"id": "1", "name": "楽観シナリオ試算", "created_at": "2026-08-01T09:00:00+00:00"},
        {"id": "2", "name": "標準シナリオ試算", "created_at": "2026-08-10T09:00:00+00:00"},
        {"id": "3", "name": "悲観シナリオ試算", "created_at": "2026-08-20T09:00:00+00:00"},
    ]


def test_filter_history_rejects_non_list_input():
    with pytest.raises(ValueError):
        filter_history({"not": "a list"})


def test_filter_history_by_keyword_matches_name_case_insensitive():
    result = filter_history(_named_records(), keyword="楽観")

    assert [item["id"] for item in result] == ["1"]


def test_filter_history_by_keyword_returns_all_when_blank():
    result = filter_history(_named_records(), keyword="   ")

    assert len(result) == 3


def test_filter_history_by_start_date():
    result = filter_history(_named_records(), start_date="2026-08-10")

    assert [item["id"] for item in result] == ["2", "3"]


def test_filter_history_by_end_date():
    result = filter_history(_named_records(), end_date="2026-08-10")

    assert [item["id"] for item in result] == ["1", "2"]


def test_filter_history_by_date_range():
    result = filter_history(
        _named_records(), start_date="2026-08-05", end_date="2026-08-15"
    )

    assert [item["id"] for item in result] == ["2"]


def test_filter_history_combines_keyword_and_date_range():
    result = filter_history(
        _named_records(),
        keyword="シナリオ",
        start_date="2026-08-15",
    )

    assert [item["id"] for item in result] == ["3"]


def test_filter_history_skips_non_dict_records():
    records = _named_records() + ["not-a-dict"]

    result = filter_history(records)

    assert len(result) == 3


def _history_record(name, cash_months=24.0, action="追加投資"):
    return {
        "name": name,
        "created_at": "2026-08-21T12:00:00+00:00",
        "results": {
            "asset_depletion_label": "余裕あり",
            "net_annual_spending": 180.0,
            "recommended_monthly_spending": 13.5,
            "cash_months": cash_months,
            "target_cash": 180.0,
            "additional_investment": 0.0,
            "investment_withdrawal": 0.0,
            "recommended_action": action,
            "pension_gap_after_start": 20.0,
            "nisa_remaining_limit": 1200.0,
            "nisa_growth_remaining_limit": 900.0,
            "nisa_annual_room": 200.0,
            "ideco_annual_contribution": 12.0,
        },
    }


def test_export_history_to_csv_contains_header_and_bom():
    csv_text = export_history_to_csv(
        [_history_record("A"), _history_record("B", cash_months=36.0)]
    )

    assert csv_text.startswith("\ufeff")
    assert "履歴名,実行日時" in csv_text
    assert "現金生活費（か月）" in csv_text
    assert "\r\n" in csv_text


def test_export_history_to_csv_includes_record_values():
    csv_text = export_history_to_csv([_history_record("Aさん", cash_months=24.0)])

    assert "Aさん,2026-08-21T12:00:00+00:00" in csv_text
    assert "24.0か月" in csv_text
    assert "追加投資" in csv_text


def test_export_history_to_csv_handles_missing_results():
    csv_text = export_history_to_csv([{"name": "結果なし"}])

    assert "結果なし" in csv_text
    assert "---" in csv_text


def test_export_history_to_csv_skips_non_dict_records():
    csv_text = export_history_to_csv([_history_record("A"), "not-a-dict"])

    lines = [line for line in csv_text.splitlines() if line]
    # ヘッダー1行 + 有効なレコード1行のみ
    assert len(lines) == 2


def test_export_history_to_csv_empty_list_returns_header_only():
    csv_text = export_history_to_csv([])

    lines = [line for line in csv_text.splitlines() if line]
    assert len(lines) == 1
    assert lines[0].startswith("\ufeff履歴名,実行日時")


def test_export_history_to_csv_rejects_non_list_input():
    with pytest.raises(ValueError):
        export_history_to_csv({"not": "a list"})


def test_history_export_filename_has_expected_prefix_and_extension():
    filename = history_export_filename()

    assert filename.startswith("fire_compass_history_")
    assert filename.endswith(".csv")


def test_clear_history(tmp_path):
    history_path = tmp_path / "history.json"

    save_history(
        {"name": "A"},
        path=history_path,
    )

    save_history(
        {"name": "B"},
        path=history_path,
    )

    clear_history(path=history_path)

    assert load_history(path=history_path) == []
