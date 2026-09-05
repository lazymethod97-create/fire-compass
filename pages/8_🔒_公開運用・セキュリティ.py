import os

import streamlit as st

from services.security import build_security_status

st.set_page_config(
    page_title="FIRE Compass 公開運用・セキュリティ",
    page_icon="🔒",
    layout="wide",
)

st.title("🔒 公開運用・セキュリティ")
st.caption("公開環境での設定状態と、履歴データの分離方針を確認するページです。")

status = build_security_status(
    env=os.environ,
    history_path=".fire_compass_history.json",
)

if not status["public_mode"]:
    st.info(
        "現在は非公開モード（ローカル個人利用）で動作しています。"
        "このページの内容は、アプリを公開サービスとして運用する場合にのみ"
        "関係します。公開運用する場合は、環境変数 "
        "`FIRE_COMPASS_PUBLIC_MODE=1` を設定してから改めてこのページを"
        "開いてください。"
    )
    st.stop()

st.success("公開モードが有効です。履歴はStreamlitセッション単位で分離されます。")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("公開モード", "有効" if status["public_mode"] else "無効")
with c2:
    st.metric("履歴の保存範囲", str(status["history_scope"]))
with c3:
    st.metric(
        "Gemini APIキー",
        "設定済み" if status["gemini_api_key_configured"] else "未設定",
    )

st.subheader("安全性チェック")
st.write("✅ APIキーそのものは画面へ表示しません。")
st.write("✅ 公開モードではセッションIDをハッシュ化して履歴ファイル名に使用します。")
st.write("✅ Streamlitセッションを取得できない場合は共有履歴ファイルへ書き込みません。")
st.write("✅ FIREの金融計算ロジックはこのSprintで変更しません。")

st.subheader("公開時の設定")
st.code("FIRE_COMPASS_PUBLIC_MODE=1", language="text")
st.caption(
    "Geminiを利用する場合は GEMINI_API_KEY も環境変数で設定してください。"
    "APIキーはソースコードや画面へ直接記載しません。"
)

st.subheader("監視について")
st.info(
    "このSprintでは、公開運用に必要な設定状態を画面で確認できるようにしました。"
    "外部の稼働監視サービスやアラート機構は、次の運用Sprintで追加できる構成です。"
)