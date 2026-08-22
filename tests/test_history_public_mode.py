from services import history_manager


def test_public_mode_separates_histories_by_session(tmp_path, monkeypatch):
    monkeypatch.setenv("FIRE_COMPASS_PUBLIC_MODE", "1")

    history_path = tmp_path / ".fire_compass_history.json"

    monkeypatch.setattr(
        history_manager,
        "_streamlit_session_suffix",
        lambda: "session_a",
    )

    save_a = history_manager.save_history(
        {"name": "ユーザーA"},
        path=history_path,
    )

    monkeypatch.setattr(
        history_manager,
        "_streamlit_session_suffix",
        lambda: "session_b",
    )

    save_b = history_manager.save_history(
        {"name": "ユーザーB"},
        path=history_path,
    )

    assert save_a["name"] == "ユーザーA"
    assert save_b["name"] == "ユーザーB"

    monkeypatch.setattr(
        history_manager,
        "_streamlit_session_suffix",
        lambda: "session_a",
    )

    history_a = history_manager.load_history(
        path=history_path,
    )

    monkeypatch.setattr(
        history_manager,
        "_streamlit_session_suffix",
        lambda: "session_b",
    )

    history_b = history_manager.load_history(
        path=history_path,
    )

    assert [record["name"] for record in history_a] == ["ユーザーA"]
    assert [record["name"] for record in history_b] == ["ユーザーB"]


def test_public_mode_creates_different_paths_for_different_sessions(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("FIRE_COMPASS_PUBLIC_MODE", "1")

    history_path = tmp_path / ".fire_compass_history.json"

    monkeypatch.setattr(
        history_manager,
        "_streamlit_session_suffix",
        lambda: "session_a",
    )
    path_a = history_manager._history_path(history_path)

    monkeypatch.setattr(
        history_manager,
        "_streamlit_session_suffix",
        lambda: "session_b",
    )
    path_b = history_manager._history_path(history_path)

    assert path_a is not None
    assert path_b is not None
    assert path_a != path_b
