from __future__ import annotations

from unittest.mock import MagicMock

from services import ui_mode


def test_default_checklist_path_points_to_project_root_file():
    path = ui_mode.default_checklist_path()

    assert path.endswith(".fire_compass_checklist.json")
    assert path.startswith(ui_mode.BASE_DIR)


def test_require_advanced_mode_does_nothing_in_advanced_mode(monkeypatch):
    monkeypatch.setattr(
        ui_mode,
        "load_checklist_state",
        lambda path=None: {"simple_mode": False, "checked_items": []},
    )
    mock_info = MagicMock()
    mock_stop = MagicMock()
    monkeypatch.setattr(ui_mode.st, "info", mock_info)
    monkeypatch.setattr(ui_mode.st, "stop", mock_stop)

    ui_mode.require_advanced_mode("このテスト機能")

    mock_info.assert_not_called()
    mock_stop.assert_not_called()


def test_require_advanced_mode_shows_guidance_and_stops_in_simple_mode(monkeypatch):
    monkeypatch.setattr(
        ui_mode,
        "load_checklist_state",
        lambda path=None: {"simple_mode": True, "checked_items": []},
    )
    mock_info = MagicMock()
    mock_stop = MagicMock()
    monkeypatch.setattr(ui_mode.st, "info", mock_info)
    monkeypatch.setattr(ui_mode.st, "stop", mock_stop)

    ui_mode.require_advanced_mode("このテスト機能")

    mock_info.assert_called_once()
    assert "このテスト機能" in mock_info.call_args[0][0]
    mock_stop.assert_called_once()


def test_require_advanced_mode_passes_custom_path_through(monkeypatch):
    received_paths = []

    def _fake_load_checklist_state(path=None):
        received_paths.append(path)
        return {"simple_mode": False, "checked_items": []}

    monkeypatch.setattr(ui_mode, "load_checklist_state", _fake_load_checklist_state)
    monkeypatch.setattr(ui_mode.st, "info", MagicMock())
    monkeypatch.setattr(ui_mode.st, "stop", MagicMock())

    ui_mode.require_advanced_mode("このテスト機能", path="/tmp/custom_checklist.json")

    assert received_paths == ["/tmp/custom_checklist.json"]