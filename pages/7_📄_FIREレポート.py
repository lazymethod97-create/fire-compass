import os

import streamlit as st

from services.history_manager import load_history
from services.report_generator import build_report_html, report_filename


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_PATH = os.path.join(BASE_DIR, ".fire_compass_history.json")


st.set_page_config(
    page_title="FIRE Compass レポート",
    page_icon="📄",
    layout="wide",
)

st.title("📄 FIREレポート")
st.caption(
    "保存済みのFIREシミュレーション結果を、読みやすいレポートとして出力します。"
)

records = load_history(path=HISTORY_PATH)

if not records:
    st.info(
        "保存済み履歴がありません。まず「FIRE Compass」画面で"
        "シミュレーションを実行して保存してください。"
    )
    st.stop()

labels = []
for index, record in enumerate(records):
    name = record.get("name", "名称未設定")
    created_at = record.get("created_at", "日時不明")
    labels.append(f"{index + 1}. {name} / {created_at}")

selected_label = st.selectbox("レポートにする履歴", labels)
selected_index = labels.index(selected_label)
selected_record = records[selected_index]

st.subheader("レポート対象")
results = selected_record.get("results", {})
c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "資産寿命判定",
        results.get("asset_depletion_label", "---"),
    )

with c2:
    st.metric(
        "推奨月間支出",
        f"{results.get('recommended_monthly_spending', 0):,.1f}万円",
    )

with c3:
    st.metric(
        "現金生活費",
        f"{results.get('cash_months', 0):,.1f}か月",
    )

st.info(
    "HTMLレポートを保存すると、ブラウザの「印刷」から"
    "「PDFとして保存」を選べます。"
)

html = build_report_html(selected_record)

st.download_button(
    label="📥 HTMLレポートをダウンロード",
    data=html,
    file_name=report_filename(selected_record),
    mime="text/html",
    use_container_width=True,
)

with st.expander("このレポートに含まれる情報"):
    st.write(
        "FIRE状態、入力条件、標準・悲観・楽観シナリオ、"
        "今月の行動候補、NISA・iDeCo・年金関連の計算結果、"
        "金融判断に関する注意事項をまとめます。"
    )
