import pytest

from services.history_manager import (
    clear_history,
    delete_history,
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
