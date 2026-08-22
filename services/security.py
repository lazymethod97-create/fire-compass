from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

PUBLIC_MODE_ENV = "FIRE_COMPASS_PUBLIC_MODE"
GEMINI_KEY_ENV = "GEMINI_API_KEY"
GEMINI_MODEL_ENV = "GEMINI_MODEL"


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def is_public_mode(env: Mapping[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    return _truthy(values.get(PUBLIC_MODE_ENV))


def build_security_status(
    *,
    env: Mapping[str, str] | None = None,
    history_path: str | Path | None = None,
) -> dict[str, object]:
    values = os.environ if env is None else env
    public_mode = is_public_mode(values)

    return {
        "public_mode": public_mode,
        "gemini_api_key_configured": bool(values.get(GEMINI_KEY_ENV)),
        "gemini_model_configured": bool(values.get(GEMINI_MODEL_ENV)),
        "history_scope": (
            "Streamlitセッション単位"
            if public_mode
            else "ローカル環境の履歴ファイル"
        ),
        "history_path": str(history_path or ".fire_compass_history.json"),
        "secret_values_exposed": False,
        "core_financial_logic_changed": False,
    }


def safe_error_message(error: BaseException) -> str:
    """内部パスやAPIキー等を表示せず、安全な利用者向け文言を返す。"""
    error_type = type(error).__name__
    if error_type in {"ValueError", "TypeError"}:
        return "入力値を確認して、もう一度実行してください。"
    return "内部処理で問題が発生しました。入力内容を確認して再試行してください。"
