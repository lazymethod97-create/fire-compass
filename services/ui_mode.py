from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from services.checklist_state import DEFAULT_CHECKLIST_PATH, load_checklist_state

# services/ui_mode.py から見て1つ上の階層（app.py・pages/ と同じ階層）が
# プロジェクトルート。checklist_state.py・app.py・pages/9・10で従来個別に
# 組み立てていたCHECKLIST_PATHを、この1箇所に統合する。
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_checklist_path() -> str:
    """プロジェクトルート直下にある既定のチェックリスト状態ファイルのパスを返す。"""
    return os.path.join(BASE_DIR, DEFAULT_CHECKLIST_PATH)


def require_advanced_mode(
    feature_label: str, path: str | Path | None = None
) -> None:
    """簡易モード中は案内文だけを表示してページの実行を止める。

    詳細モード（simple_mode=False）の場合は何もせず呼び出し元へ戻り、
    ページ本来の処理をそのまま続行させる。

    pages/配下の各ページの先頭付近から呼び出すことを想定したガード関数。
    simple_modeの判定・案内文・st.stop()の呼び出しをこの1関数に集約する
    ことで、新しいページを追加する場合もこのガードを1行呼ぶだけで従来と
    同じ挙動になる（各ページ側でCHECKLIST_PATHを再定義する必要もない）。

    Args:
        feature_label: 案内文に差し込む機能名（例:「この比較機能」）。
        path: チェックリスト状態ファイルのパス。省略時はプロジェクト直下の
            既定ファイル（default_checklist_path()）を使う。
    """
    checklist_path = path if path is not None else default_checklist_path()

    if not load_checklist_state(path=checklist_path)["simple_mode"]:
        return

    st.info(
        f"現在は簡易モードです。{feature_label}は詳細モードでのみ使用できます。"
        "「FIRE Compass」画面上部の「🗂️ 簡易モード」トグルをオフにしてから、"
        "改めてこのページを開いてください。"
    )
    st.stop()