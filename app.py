import streamlit as st
from services.fire_engine import FireInput, run_fire_simulation

st.set_page_config(
    page_title="FIRE Compass",
    page_icon="🧭",
    layout="wide",
)

st.title("🧭 FIRE Compass")
st.caption("FIRE後の生活費・資産寿命・取り崩し余力をシミュレーションするアプリ")

st.subheader("1. FIRE基本情報")

c1, c2, c3 = st.columns(3)
with c1:
    current_age = st.number_input("現在年齢", min_value=18, max_value=100, value=43)
with c2:
    end_age = st.number_input("シミュレーション終了年齢", min_value=50, max_value=120, value=90)
with c3:
    current_assets = st.number_input(
        "現在の総金融資産（万円）", min_value=0.0, value=4700.0, step=50.0
    )

c4, c5, c6 = st.columns(3)
with c4:
    cash_assets = st.number_input(
        "現金・預金（万円）", min_value=0.0, value=800.0, step=50.0
    )
with c5:
    annual_spending = st.number_input(
        "年間生活費（万円）", min_value=0.0, value=200.0, step=10.0
    )
with c6:
    annual_side_income = st.number_input(
        "年間副収入（万円）", min_value=0.0, value=36.0, step=5.0
    )

st.subheader("2. シミュレーション条件")

c7, c8, c9 = st.columns(3)
with c7:
    expected_return = st.number_input(
        "想定運用利回り（%）", min_value=-20.0, max_value=20.0, value=4.0, step=0.5
    )
with c8:
    inflation = st.number_input(
        "想定インフレ率（%）", min_value=0.0, max_value=10.0, value=2.0, step=0.5
    )
with c9:
    safety_margin = st.slider(
        "安全余裕率（%）", min_value=0, max_value=40, value=10, step=5
    )

run = st.button("🧭 FIREシミュレーションを実行", type="primary", use_container_width=True)

if run:
    result = run_fire_simulation(
        FireInput(
            current_age=current_age,
            end_age=end_age,
            total_assets=current_assets,
            cash_assets=cash_assets,
            annual_spending=annual_spending,
            annual_side_income=annual_side_income,
            expected_return_pct=expected_return,
            inflation_pct=inflation,
            safety_margin_pct=safety_margin,
        )
    )

    st.subheader("3. 現在のFIRE状態")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("純年間支出", f"{result.net_annual_spending:,.0f}万円")
    m2.metric("推奨月間支出", f"{result.recommended_monthly_spending:,.1f}万円")
    m3.metric("現金生活費", f"{result.cash_months:.1f}か月")
    m4.metric("資産寿命", result.asset_depletion_label)

    st.info(result.advice)

    st.subheader("4. 資産推移")

    chart_df = result.yearly_df.set_index("age")[["standard", "bear", "bull"]]
    chart_df.columns = ["標準", "悲観", "楽観"]
    st.line_chart(chart_df, use_container_width=True)

    st.subheader("5. シナリオ結果")

    scenario_cols = st.columns(3)
    for col, scenario in zip(scenario_cols, result.scenario_summaries):
        with col:
            st.markdown(f"### {scenario.name}")
            st.write(f"終了時資産: **{scenario.final_assets:,.0f}万円**")
            st.write(f"最低資産: **{scenario.min_assets:,.0f}万円**")
            st.write(f"資産枯渇: **{scenario.depleted_at}**")
else:
    st.markdown(
        """
### このアプリで分かること
- 今の資産と収入なら、月にいくら使えるか
- 現金だけで何か月生活できるか
- 想定利回り・インフレを踏まえた資産寿命
- 標準・悲観・楽観シナリオでの資産推移

> ※現在はSprint 1のシミュレーション版です。実際の売買判断を自動で行う機能は、後続Sprintで追加します。
"""
    )
