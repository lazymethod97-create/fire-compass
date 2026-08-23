import os

import streamlit as st

from services.app_logger import clear_events, load_events

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENT_LOG_PATH = os.path.join(BASE_DIR, ".fire_compass_events.log")

LEVEL_ICON = {
    "INFO": "🟢",
    "WARNING": "🟡",
    "ERROR": "🔴",
}

st.set_page_config(
    page_title="FIRE Compass ログ・監視",
    page_icon="📋",
    layout="wide",
)

st.title("📋 ログ・監視")
st.caption(
    "アプリの動作イベントやエラーの発生状況を、このローカル環境内だけで確認できます。"
    "外部サービスへの送信は行いません。"
)

level_filter = st.selectbox(
    "表示するレベル",
    ["すべて", "ERROR", "WARNING", "INFO"],
)

selected_level = None if level_filter == "すべて" else level_filter

events = load_events(
    path=EVENT_LOG_PATH,
    level=selected_level,
)

all_events = load_events(path=EVENT_LOG_PATH)
error_count = len([e for e in all_events if e.get("level") == "ERROR"])
warning_count = len([e for e in all_events if e.get("level") == "WARNING"])
info_count = len([e for e in all_events if e.get("level") == "INFO"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("記録件数（最新500件まで）", len(all_events))
c2.metric("🔴 エラー", error_count)
c3.metric("🟡 警告", warning_count)
c4.metric("🟢 情報", info_count)

st.subheader("イベント一覧")

if not events:
    st.info("表示できるログはまだありません。")
else:
    for event in events:
        icon = LEVEL_ICON.get(event.get("level", "INFO"), "⚪")
        with st.container(border=True):
            st.write(
                f"{icon} **{event.get('event_type', '不明')}**"
                f"　`{event.get('timestamp', '日時不明')}`"
            )
            st.caption(event.get("message", ""))

st.divider()

st.subheader("ログの管理")
st.write(
    "ログは `.fire_compass_events.log` にローカル保存され、"
    "Gitの管理対象からは除外されています。最新500件を超えると古い記録から自動的に削除されます。"
)

if st.button("🗑️ ログを全て削除", use_container_width=True):
    clear_events(path=EVENT_LOG_PATH)
    st.success("ログを削除しました。")
    st.rerun()

st.info(
    "このページで確認できるのは、シミュレーション実行や履歴の保存・削除、"
    "AIアドバイスがルールベースへフォールバックした理由などのアプリ内イベントです。"
    "金融計算の結果そのものは変更・記録しません。"
)
