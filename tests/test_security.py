from services.security import build_security_status, is_public_mode, safe_error_message


def test_public_mode_accepts_common_truthy_values():
    assert is_public_mode({"FIRE_COMPASS_PUBLIC_MODE": "1"}) is True
    assert is_public_mode({"FIRE_COMPASS_PUBLIC_MODE": "true"}) is True
    assert is_public_mode({"FIRE_COMPASS_PUBLIC_MODE": "on"}) is True


def test_public_mode_is_false_by_default():
    assert is_public_mode({}) is False


def test_security_status_does_not_expose_secret_values():
    status = build_security_status(
        env={
            "FIRE_COMPASS_PUBLIC_MODE": "1",
            "GEMINI_API_KEY": "super-secret",
        }
    )
    assert status["public_mode"] is True
    assert status["gemini_api_key_configured"] is True
    assert status["secret_values_exposed"] is False
    assert "super-secret" not in str(status)


def test_public_history_scope_is_session_based():
    status = build_security_status(env={"FIRE_COMPASS_PUBLIC_MODE": "1"})
    assert status["history_scope"] == "Streamlitセッション単位"


def test_safe_error_message_hides_internal_details():
    error = RuntimeError("C:\\secret\\service-account.json GEMINI_API_KEY=abc")
    message = safe_error_message(error)
    assert "secret" not in message
    assert "GEMINI_API_KEY" not in message
    assert "abc" not in message
