import os

import streamlit as st

from services.app_logger import (
    clear_events,
    events_export_filename,
    export_events_to_csv,
    filter_events,
    load_events,
)

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

if st.session_state.get("simple_mode", True):
    st.info(
        "現在は簡易モードです。このログ・監視機能は詳細モードでのみ"
        "使用できます。「FIRE Compass」画面上部の「🗂️ 簡易モード」"
        "トグルをオフにしてから、改めてこのページを開いてください。"
    )
    st.stop()

level_filter = st.selectbox(
    "表示するレベル",
    ["すべて", "ERROR", "WARNING", "INFO"],
)

selected_level = None if level_filter == "すべて" else level_filter

keyword_filter = st.text_input(
    "キーワード検索（イベント種別・メッセージを対象）",
    value="",
    placeholder="例: simulation_executed / フォールバック",
)

date_col1, date_col2 = st.columns(2)
with date_col1:
    start_date = st.date_input(
        "開始日（この日を含む）",
        value=None,
        key="log_start_date",
    )
with date_col2:
    end_date = st.date_input(
        "終了日（この日を含む）",
        value=None,
        key="log_end_date",
    )

events = load_events(
    path=EVENT_LOG_PATH,
    level=selected_level,
)

events = filter_events(
    events,
    keyword=keyword_filter,
    start_date=str(start_date) if start_date else None,
    end_date=str(end_date) if end_date else None,
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
st.caption(f"絞り込み後の件数: {len(events)}件")

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

st.subheader("ログのエクスポート")
st.write(
    "現在表示中の絞り込み結果（レベル・キーワード・期間）のログを、"
    "Excel等で開けるCSVファイルとしてダウンロードできます。"
)

csv_data = export_events_to_csv(events)

st.download_button(
    label="📥 表示中のログをCSVでダウンロード",
    data=csv_data,
    file_name=events_export_filename(selected_level),
    mime="text/csv",
    use_container_width=True,
    disabled=not events,
)

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