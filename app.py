import os

import streamlit as st
from dotenv import load_dotenv

from services.ai_advisor import generate_ai_advice
from services.action_engine import calculate_monthly_action
from services.crash_strategy import calculate_crash_strategy
from services.fire_engine import FireInput, run_fire_simulation
from services.tax_optimization import TaxOptimizationInput, run_tax_optimization

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
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
    current_age = st.number_input(
        "現在年齢",
        min_value=18,
        max_value=100,
        value=43,
    )

with c2:
    end_age = st.number_input(
        "シミュレーション終了年齢",
        min_value=50,
        max_value=120,
        value=90,
    )

with c3:
    current_assets = st.number_input(
        "現在の総金融資産（万円）",
        min_value=0.0,
        value=4700.0,
        step=50.0,
    )

c4, c5, c6 = st.columns(3)

with c4:
    cash_assets = st.number_input(
        "現金・預金（万円）",
        min_value=0.0,
        value=800.0,
        step=50.0,
    )

with c5:
    annual_spending = st.number_input(
        "年間生活費（万円）",
        min_value=0.0,
        value=200.0,
        step=10.0,
    )

with c6:
    annual_side_income = st.number_input(
        "年間副収入（万円）",
        min_value=0.0,
        value=36.0,
        step=5.0,
    )

st.subheader("2. シミュレーション条件")

c7, c8, c9 = st.columns(3)

with c7:
    expected_return = st.number_input(
        "想定運用利回り（%）",
        min_value=-20.0,
        max_value=20.0,
        value=4.0,
        step=0.5,
    )

with c8:
    inflation = st.number_input(
        "想定インフレ率（%）",
        min_value=0.0,
        max_value=10.0,
        value=2.0,
        step=0.5,
    )

with c9:
    safety_margin = st.slider(
        "安全余裕率（%）",
        min_value=0,
        max_value=40,
        value=10,
        step=5,
    )

st.subheader("3. 現金バッファ・市場環境")

c10, c11 = st.columns(2)

with c10:
    min_cash_months = st.number_input(
        "最低確保する現金（か月）",
        min_value=0.0,
        max_value=36.0,
        value=12.0,
        step=1.0,
        help="通常時に最低限確保したい現金の月数です。",
    )

with c11:
    market_condition = st.selectbox(
        "現在の市場環境",
        ["通常", "弱気相場", "暴落", "深刻な暴落"],
    )

run = st.button(
    "🧭 FIREシミュレーションを実行",
    type="primary",
    use_container_width=True,
)

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

    base_action = calculate_monthly_action(
        cash_assets=cash_assets,
        total_assets=current_assets,
        net_annual_spending=result.net_annual_spending,
        min_cash_months=min_cash_months,
    )

    strategy = calculate_crash_strategy(
        base_monthly_spending=result.net_annual_spending / 12.0,
        min_cash_months=min_cash_months,
        condition=market_condition,
    )

    target_cash = (
        result.net_annual_spending
        / 12.0
        * strategy.target_cash_months
    )

    investment_assets = max(current_assets - cash_assets, 0.0)

    cash_surplus = max(cash_assets - target_cash, 0.0)
    cash_shortage = max(target_cash - cash_assets, 0.0)

    additional_investment = round(
        cash_surplus * strategy.additional_investment_ratio,
        2,
    )

    investment_withdrawal = round(
        min(cash_shortage, investment_assets),
        2,
    )

    if investment_withdrawal > 0:
        recommended_action = "投資資産から現金を補充"
    elif additional_investment > 0:
        recommended_action = "追加投資"
    else:
        recommended_action = "取り崩し・追加投資は不要"

    st.subheader("4. 今月の推奨行動")

    st.success(
        f"**{strategy.label}：{recommended_action}**"
    )

    a1, a2, a3, a4 = st.columns(4)

    a1.metric(
        "目標現金",
        f"{target_cash:,.1f}万円",
    )

    a2.metric(
        "追加投資額",
        f"{additional_investment:,.1f}万円",
    )

    a3.metric(
        "取り崩し額",
        f"{investment_withdrawal:,.1f}万円",
    )

    a4.metric(
        "推奨月間生活費",
        f"{strategy.recommended_monthly_spending:,.1f}万円",
    )

    st.info(strategy.reason)

    st.caption(
        "Sprint 3では、市場環境に応じて現金バッファ・生活費・追加投資ルールを調整します。"
        "総資産シミュレーションそのものには二重計上しません。"
    )

    st.subheader("5. 市場環境別の防御ルール")

    rule_cols = st.columns(4)

    for col, condition in zip(
        rule_cols,
        ["通常", "弱気相場", "暴落", "深刻な暴落"],
    ):
        condition_strategy = calculate_crash_strategy(
            base_monthly_spending=result.net_annual_spending / 12.0,
            min_cash_months=min_cash_months,
            condition=condition,
        )

        with col:
            st.markdown(f"### {condition}")
            st.write(
                f"現金：**{condition_strategy.target_cash_months:.0f}か月**"
            )
            st.write(
                f"追加投資：**"
                f"{condition_strategy.additional_investment_ratio * 100:.0f}%**"
            )
            st.write(
                f"生活費削減：**"
                f"{condition_strategy.spending_reduction_pct:.0f}%**"
            )

    st.subheader("6. AI FIREアドバイス")

    ai_advice = generate_ai_advice(
        fire_result=result,
        market_condition=market_condition,
        strategy=strategy,
        recommended_action=recommended_action,
        additional_investment=additional_investment,
        investment_withdrawal=investment_withdrawal,
    )

    st.markdown(ai_advice)
    st.subheader("7. NISA・iDeCo・年金最適化")

    t1, t2, t3 = st.columns(3)

    with t1:
        nisa_assets = st.number_input(
            "NISA現在残高（万円）",
            min_value=0.0,
            value=0.0,
            step=10.0,
        )
        nisa_contributed = st.number_input(
            "NISA累計投資額・簿価（万円）",
            min_value=0.0,
            value=0.0,
            step=10.0,
            help="NISAの非課税保有限度額は取得価額（簿価）ベースです。",
        )
        nisa_growth_contributed = st.number_input(
            "うち成長投資枠の累計投資額（万円）",
            min_value=0.0,
            value=0.0,
            step=10.0,
        )
        nisa_annual_contributed = st.number_input(
            "今年のNISA投資額（万円）",
            min_value=0.0,
            value=0.0,
            step=10.0,
        )

    with t2:
        taxable_assets = st.number_input(
            "課税口座残高（万円）",
            min_value=0.0,
            value=0.0,
            step=10.0,
        )
        ideco_assets = st.number_input(
            "iDeCo現在残高（万円）",
            min_value=0.0,
            value=0.0,
            step=10.0,
        )
        ideco_monthly_contribution = st.number_input(
            "iDeCo月額掛金（万円）",
            min_value=0.0,
            value=0.0,
            step=0.1,
        )
        ideco_annual_limit = st.number_input(
            "iDeCo年間上限（万円）",
            min_value=0.0,
            value=74.4,
            step=1.0,
            help="2026年12月1日施行予定の制度改正後の第2号加入者の共通拠出限度額を年額換算した参考値です。実際の上限は加入区分等で異なります。",
        )

    with t3:
        annual_pension = st.number_input(
            "65歳時点の年金見込額（万円/年）",
            min_value=0.0,
            value=0.0,
            step=10.0,
        )
        pension_start_age = st.number_input(
            "年金受給開始年齢",
            min_value=65,
            max_value=75,
            value=65,
            step=1,
        )

    tax_result = run_tax_optimization(
        TaxOptimizationInput(
            nisa_assets=nisa_assets,
            nisa_contributed=nisa_contributed,
            nisa_growth_contributed=nisa_growth_contributed,
            nisa_annual_contributed=nisa_annual_contributed,
            taxable_assets=taxable_assets,
            ideco_assets=ideco_assets,
            ideco_monthly_contribution=ideco_monthly_contribution,
            ideco_annual_limit=ideco_annual_limit,
            current_age=current_age,
            pension_start_age=pension_start_age,
            annual_pension=annual_pension,
            annual_spending=annual_spending,
            end_age=end_age,
        )
    )

    tax_cols = st.columns(5)
    tax_cols[0].metric(
        "NISA残り総枠",
        f"{tax_result.nisa_remaining_limit:,.0f}万円",
    )
    tax_cols[1].metric(
        "NISA成長枠残り",
        f"{tax_result.nisa_growth_remaining_limit:,.0f}万円",
    )
    tax_cols[2].metric(
        "今年のNISA残り",
        f"{tax_result.nisa_annual_room:,.0f}万円",
    )
    tax_cols[3].metric(
        "iDeCo年額拠出",
        f"{tax_result.ideco_annual_contribution:,.1f}万円",
    )
    tax_cols[4].metric(
        "年金開始後の年間不足",
        f"{tax_result.pension_gap_after_start:,.0f}万円",
    )

    st.info(tax_result.recommendation)
    st.caption(
        "NISAは年間360万円・生涯1,800万円（成長投資枠は1,200万円が内数）を基準に計算します。"
        "年金は65〜75歳の受給開始年齢を入力し、開始後の生活費不足額を表示します。"
    )

    st.subheader("8. 現在のFIRE状態")

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "純年間支出",
        f"{result.net_annual_spending:,.0f}万円",
    )

    m2.metric(
        "推奨月間支出",
        f"{result.recommended_monthly_spending:,.1f}万円",
    )

    m3.metric(
        "現金生活費",
        f"{result.cash_months:.1f}か月",
    )

    m4.metric(
        "資産寿命",
        result.asset_depletion_label,
    )

    st.info(result.advice)

    st.subheader("9. 資産推移")

    chart_df = result.yearly_df.set_index("age")[
        ["standard", "bear", "bull"]
    ]

    chart_df.columns = [
        "標準",
        "悲観",
        "楽観",
    ]

    st.line_chart(
        chart_df,
        use_container_width=True,
    )

    st.subheader("10. シナリオ結果")

    scenario_cols = st.columns(3)

    for col, scenario in zip(
        scenario_cols,
        result.scenario_summaries,
    ):
        with col:
            st.markdown(f"### {scenario.name}")

            st.write(
                f"終了時資産：**{scenario.final_assets:,.0f}万円**"
            )

            st.write(
                f"最低資産：**{scenario.min_assets:,.0f}万円**"
            )

            st.write(
                f"資産枯渇：**{scenario.depleted_at}**"
            )

else:
    st.markdown(
        """
### このアプリで分かること

- 今の資産と収入なら、月にいくら使えるか
- 現金だけで何か月生活できるか
- 最低現金バッファを何か月分にするか
- 市場環境に応じて現金バッファをどこまで増やすか
- 弱気相場や暴落時に追加投資をどこまで抑えるか
- 暴落時に月間生活費をどこまで調整するか
- 想定利回り・インフレを踏まえた資産寿命

> ※このアプリは金融商品の売買を自動で決定するものではなく、
> 入力条件に基づくシミュレーションと行動候補を表示します。
"""
    )

