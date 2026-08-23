import pytest

from services import app_logger


def test_log_event_writes_and_returns_entry(tmp_path):
    log_path = tmp_path / "events.log"

    entry = app_logger.log_event(
        "simulation_executed",
        "FIREシミュレーションを実行しました。",
        path=log_path,
    )

    assert entry is not None
    assert entry["event_type"] == "simulation_executed"
    assert entry["level"] == "INFO"
    assert log_path.exists()


def test_log_event_requires_event_type(tmp_path):
    with pytest.raises(ValueError):
        app_logger.log_event("", "message", path=tmp_path / "events.log")


def test_log_event_normalizes_invalid_level(tmp_path):
    log_path = tmp_path / "events.log"

    entry = app_logger.log_event(
        "ai_advice_fallback",
        "fallback reason",
        level="not-a-real-level",
        path=log_path,
    )

    assert entry["level"] == "INFO"


def test_log_event_accepts_lowercase_level(tmp_path):
    log_path = tmp_path / "events.log"

    entry = app_logger.log_event(
        "ai_advice_fallback",
        "fallback reason",
        level="error",
        path=log_path,
    )

    assert entry["level"] == "ERROR"


def test_load_events_filters_by_level(tmp_path):
    log_path = tmp_path / "events.log"

    app_logger.log_event("a", "info event", level="INFO", path=log_path)
    app_logger.log_event("b", "warn event", level="WARNING", path=log_path)
    app_logger.log_event("c", "error event", level="ERROR", path=log_path)

    errors = app_logger.load_events(path=log_path, level="ERROR")

    assert len(errors) == 1
    assert errors[0]["event_type"] == "c"


def test_load_events_returns_most_recent_first(tmp_path):
    log_path = tmp_path / "events.log"

    app_logger.log_event("first", "1", path=log_path)
    app_logger.log_event("second", "2", path=log_path)

    events = app_logger.load_events(path=log_path)

    assert [item["event_type"] for item in events] == ["second", "first"]


def test_max_events_caps_stored_entries(tmp_path):
    log_path = tmp_path / "events.log"

    for index in range(5):
        app_logger.log_event(
            f"event_{index}",
            "msg",
            path=log_path,
            max_events=3,
        )

    events = app_logger.load_events(path=log_path, limit=100)

    assert len(events) == 3
    assert [item["event_type"] for item in events] == [
        "event_4",
        "event_3",
        "event_2",
    ]


def test_load_events_with_missing_file_returns_empty_list(tmp_path):
    log_path = tmp_path / "does_not_exist.log"

    assert app_logger.load_events(path=log_path) == []


def test_load_events_rejects_invalid_limit(tmp_path):
    with pytest.raises(ValueError):
        app_logger.load_events(path=tmp_path / "events.log", limit=0)


def test_clear_events_removes_log_file(tmp_path):
    log_path = tmp_path / "events.log"

    app_logger.log_event("a", "msg", path=log_path)
    assert log_path.exists()

    app_logger.clear_events(path=log_path)

    assert not log_path.exists()


def test_clear_events_on_missing_file_does_not_raise(tmp_path):
    log_path = tmp_path / "does_not_exist.log"

    app_logger.clear_events(path=log_path)
