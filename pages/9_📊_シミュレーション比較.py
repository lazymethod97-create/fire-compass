import os

import streamlit as st

from services.comparison_engine import (
    MAX_RECORDS,
    MIN_RECORDS,
    build_comparison,
    comparison_export_filename,
    export_comparison_to_csv,
    format_comparison_value,
)
from services.history_manager import load_history
from services.security import safe_error_message

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_PATH = os.path.join(BASE_DIR, ".fire_compass_history.json")


st.set_page_config(
    page_title="FIRE Compass 比較",
    page_icon="📊",
    layout="wide",
)

st.title("📊 シミュレーション比較")
st.caption(
    "保存済みのシミュレーション履歴を2〜4件選んで、主要な指標を並べて比較します。"
)

if st.session_state.get("simple_mode", True):
    st.info(
        "現在は簡易モードです。この比較機能は詳細モードでのみ使用できます。"
        "「FIRE Compass」画面上部の「🗂️ 簡易モード」トグルをオフにしてから、"
        "改めてこのページを開いてください。"
    )
    st.stop()

records = load_history(path=HISTORY_PATH)

if len(records) < MIN_RECORDS:
    st.info(
        "比較には履歴が2件以上必要です。まず「FIRE Compass」画面で"
        "シミュレーションを実行し、複数件保存してください。"
    )
    st.stop()

labels = []
for index, record in enumerate(records):
    name = record.get("name", "名称未設定")
    created_at = record.get("created_at", "日時不明")
    labels.append(f"{index + 1}. {name} / {created_at}")

selected_labels = st.multiselect(
    f"比較する履歴を選択してください（{MIN_RECORDS}〜{MAX_RECORDS}件）",
    labels,
    default=labels[:MIN_RECORDS],
)

if len(selected_labels) < MIN_RECORDS:
    st.info(f"比較するには{MIN_RECORDS}件以上選択してください。")
    st.stop()

if len(selected_labels) > MAX_RECORDS:
    st.warning(
        f"比較できる履歴は最大{MAX_RECORDS}件までです。先頭{MAX_RECORDS}件で比較します。"
    )
    selected_labels = selected_labels[:MAX_RECORDS]

selected_records = [records[labels.index(label)] for label in selected_labels]

try:
    comparison = build_comparison(selected_records)
except ValueError as error:
    st.error(safe_error_message(error))
    st.stop()

st.subheader("比較対象")

header_cols = st.columns(len(comparison.names))
for col, name, created_at in zip(
    header_cols, comparison.names, comparison.created_ats
):
    with col:
        st.markdown(f"**{name}**")
        st.caption(created_at)

st.subheader("主要指標の比較")

table_header = "| 指標 | " + " | ".join(comparison.names) + " |"
table_divider = "|---|" + "---|" * len(comparison.names)
table_rows = []

for row in comparison.rows:
    cells = [
        format_comparison_value(value, diff, row.unit)
        for value, diff in zip(row.values, row.diffs)
    ]

    table_rows.append(f"| {row.label} | " + " | ".join(cells) + " |")

st.markdown("\n".join([table_header, table_divider, *table_rows]))

st.caption(
    f"（）内の差分は、先頭の「{comparison.names[0]}」を基準にした差です。"
)

st.divider()

st.subheader("比較結果のエクスポート")
st.write(
    "この比較表を、Excel等で開けるCSVファイルとしてダウンロードできます。"
)

st.download_button(
    label="📥 比較結果をCSVでダウンロード",
    data=export_comparison_to_csv(comparison),
    file_name=comparison_export_filename(),
    mime="text/csv",
    use_container_width=True,
)

st.info(
    "この比較は保存済みシミュレーション結果を並べて表示するものであり、"
    "金融商品の売買や特定の投資行動を断定するものではありません。"
)