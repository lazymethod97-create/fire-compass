from __future__ import annotations

import hashlib
import json
from pathlib import Path

from services.security import is_public_mode as _shared_is_public_mode

DEFAULT_CHECKLIST_PATH = ".fire_compass_checklist.json"

# 月次チェックリストの項目定義。(id, ラベル) のタプル。
# 表示順はこの並び順に従う。項目を追加・変更する場合はここだけ触ればよい。
CHECKLIST_ITEMS: list[tuple[str, str]] = [
    ("assets_updated", "資産残高を最新化した（CSV取込 or 手入力）"),
    ("simulation_run", "実行してFIRE判定を確認した"),
    ("recommendation_checked", "今月の推奨行動を確認した"),
    ("actual_spending_logged", "実際に使った金額を実績記録（12.5）に入力した"),
    ("nisa_ideco_checked", "NISA/iDeCoの枠の余りを確認した"),
]

DEFAULT_STATE: dict = {
    "simple_mode": True,
    "checked_items": [],
}


def _streamlit_session_suffix() -> str | None:
    # history_manager._streamlit_session_suffix() と同じロジック
    # （公開モード時にセッションごとに状態ファイルを分離するため）。
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        ctx = get_script_run_ctx()
        session_id = getattr(ctx, "session_id", None) if ctx else None

        if not session_id:
            return None

        return hashlib.sha256(
            session_id.encode("utf-8")
        ).hexdigest()[:16]
    except Exception:
        return None


def _checklist_path(path: str | Path | None = None) -> Path | None:
    base_path = Path(path or DEFAULT_CHECKLIST_PATH)

    if not _shared_is_public_mode():
        return base_path

    suffix = _streamlit_session_suffix()
    if not suffix:
        return None

    return base_path.with_name(
        f"{base_path.stem}_{suffix}{base_path.suffix}"
    )


def load_checklist_state(path: str | Path | None = None) -> dict:
    """チェックリストのチェック状態と表示モード（簡易/詳細）を読み込む。

    ファイルが存在しない・壊れている場合はDEFAULT_STATEのコピーを返す。
    金融計算やAIアドバイスのロジックには一切関与しない、表示状態専用の関数。
    """
    file_path = _checklist_path(path)

    if file_path is None or not file_path.exists():
        return dict(DEFAULT_STATE)

    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULT_STATE)

    if not isinstance(raw, dict):
        return dict(DEFAULT_STATE)

    state = dict(DEFAULT_STATE)
    state["simple_mode"] = bool(raw.get("simple_mode", True))

    valid_ids = {item_id for item_id, _ in CHECKLIST_ITEMS}
    checked = raw.get("checked_items", [])
    if isinstance(checked, list):
        state["checked_items"] = [
            item_id for item_id in checked if item_id in valid_ids
        ]

    return state


def save_checklist_state(state: dict, path: str | Path | None = None) -> None:
    """チェックリストのチェック状態と表示モードを保存する。"""
    if not isinstance(state, dict):
        raise ValueError("stateはdict形式で指定してください。")

    file_path = _checklist_path(path)

    if file_path is None:
        # 公開モードでセッションIDが取得できない場合は保存をスキップする
        # （history_manager.save_historyの挙動と同じ方針）。
        return

    file_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "simple_mode": bool(state.get("simple_mode", True)),
        "checked_items": list(state.get("checked_items", [])),
    }

    file_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def reset_checklist_items(path: str | Path | None = None) -> dict:
    """チェック状態だけをクリアする（表示モードの設定は維持する）。

    「今月分のチェックをリセットしたい」手動ボタン用。
    戻り値は更新後のstate。
    """
    state = load_checklist_state(path=path)
    state["checked_items"] = []
    save_checklist_state(state, path=path)
    return state
