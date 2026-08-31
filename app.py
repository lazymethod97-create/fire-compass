import os
from datetime import date

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from services.ai_advisor import generate_ai_advice, generate_portfolio_commentary
from services.action_engine import calculate_monthly_action
from services.app_logger import log_event
from services.crash_strategy import calculate_crash_strategy
from services.fire_engine import FireInput, run_fire_simulation
from services.large_expense_engine import (
    CATEGORIES as LARGE_EXPENSE_CATEGORIES,
    add_large_expense,
    delete_large_expense,
    distribution_end_month,
    load_large_expenses,
    total_for_month,
)
from services.market_data_engine import MarketDataError, fetch_market_condition
from services.monthly_budget_engine import calculate_monthly_budget
from services.budget_explanation import build_budget_explanation
from services.judgment_trend_engine import load_judgment_trend, record_monthly_judgment
from services.sequence_risk_engine import calculate_sequence_risk_factor
from services.withdrawal_engine import calculate_withdrawal_plan
from services.history_manager import (
    clear_history,
    delete_history,
    export_history_to_csv,
    filter_history,
    history_export_filename,
    load_history,
    rename_history,
    save_history,
)
from services.tax_optimization import TaxOptimizationInput, run_tax_optimization
from services.asset_import_engine import (
    AssetImportError,
    decode_csv_bytes,
    parse_sbi_fund_holdings_csv,
)
from services.portfolio_balance_engine import analyze_portfolio_balance

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_PATH = os.path.join(BASE_DIR, ".fire_compass_history.json")
EVENT_LOG_PATH = os.path.join(BASE_DIR, ".fire_compass_events.log")
LARGE_EXPENSE_PATH = os.path.join(BASE_DIR, ".fire_compass_large_expenses.json")
JUDGMENT_TREND_PATH = os.path.join(BASE_DIR, ".fire_compass_judgment_trend.json")
load_dotenv(os.path.join(BASE_DIR, ".env"))
st.set_page_config(
    page_title="FIRE Compass",
    page_icon="🧭",
    layout="wide",
)

def _safe_log_event(event_type: str, message: str, level: str = "INFO") -> None:
    """イベントログの記録に失敗しても、アプリ本体の動作は止めない。"""
    try:
        log_event(
            event_type,
            message,
            level=level,
            path=EVENT_LOG_PATH,
        )
    except Exception:
        pass


@st.cache_data(ttl=3600)
def _cached_fetch_market_condition():
    """市場データの自動取得結果を1時間キャッシュする。

    yfinanceは非公式ライブラリのためAPI呼び出しの安定性が保証されておらず、
    また画面の再描画のたびに毎回問い合わせるとレート制限に触れやすいため、
    キャッシュを挟む。取得に失敗した場合、Streamlitはこの結果をキャッシュ
    しないため、次回の再描画で再試行される。
    """
    return fetch_market_condition()


st.title("🧭 FIRE Compass")
st.caption("FIRE後の「今月いくら使っていいか・どこから取り崩すか」を判断するためのアプリ")

st.subheader("0. 保有資産の取り込み（証券会社CSV）")
st.caption(
    "SBI証券の「保有ファンド一覧」CSVをアップロードすると、下の"
    "「課税口座残高」「NISA現在残高」「NISA累計投資額・簿価」"
    "「うち成長投資枠の累計投資額」の初期値に反映します。"
    "現金・iDeCoの残高、今年のNISA投資額はCSVに含まれないため、"
    "引き続き手入力してください。"
)

uploaded_asset_csv = st.file_uploader(
    "保有ファンド一覧CSV（SBI証券）",
    type="csv",
    key="asset_import_csv",
)

if uploaded_asset_csv is not None:
    if uploaded_asset_csv.file_id != st.session_state.get(
        "_asset_import_processed_id"
    ):
        try:
            csv_text = decode_csv_bytes(uploaded_asset_csv.getvalue())
            import_result = parse_sbi_fund_holdings_csv(csv_text)
        except AssetImportError as error:
            st.error(f"CSVの取り込みに失敗しました: {error}")
            st.session_state.pop("_asset_import_processed_id", None)
            st.session_state.pop("_asset_import_result", None)
        else:
            st.session_state["taxable_assets"] = import_result.taxable_assets
            st.session_state["nisa_assets"] = import_result.nisa_assets
            st.session_state["nisa_contributed"] = import_result.nisa_contributed
            st.session_state["nisa_growth_contributed"] = (
                import_result.nisa_growth_contributed
            )
            st.session_state["_asset_import_processed_id"] = (
                uploaded_asset_csv.file_id
            )
            st.session_state["_asset_import_result"] = import_result

            balance_result = analyze_portfolio_balance(import_result.holdings)
            st.session_state["_asset_import_balance"] = balance_result
            with st.spinner("保有ファンドのバランスを評価しています..."):
                st.session_state["_asset_import_commentary"] = (
                    generate_portfolio_commentary(balance_result)
                )

            _safe_log_event(
                "asset_csv_imported",
                f"保有ファンドCSVを取り込みました（{len(import_result.holdings)}件）。",
            )

    cached_import_result = st.session_state.get("_asset_import_result")
    if cached_import_result is not None:
        combined_investment_total = round(
            cached_import_result.taxable_assets + cached_import_result.nisa_assets, 2
        )
        st.success(
            f"{len(cached_import_result.holdings)}件の保有ファンドを取り込み済みです。"
            f"課税口座残高: {cached_import_result.taxable_assets:,.1f}万円 / "
            f"NISA残高: {cached_import_result.nisa_assets:,.1f}万円 / "
            f"NISA累計投資額: {cached_import_result.nisa_contributed:,.1f}万円"
            f"（うち成長投資枠: {cached_import_result.nisa_growth_contributed:,.1f}万円）"
        )
        st.caption(
            f"課税口座＋NISAの合計は{combined_investment_total:,.1f}万円です。"
            "現金・iDeCoの残高と合わせて、必要であれば「現在の総金融資産」欄を"
            "ご確認・更新してください（自動では上書きしません）。"
            "下の入力欄は取り込み後も手動で調整できます。"
        )

        for warning in cached_import_result.warnings:
            st.caption(f"⚠️ {warning}")

        with st.expander("取り込んだファンドの内訳を見る"):
            for holding in cached_import_result.holdings:
                st.write(
                    f"- {holding.fund_name}（{holding.account_type}）："
                    f"評価額 {holding.valuation_amount:,.1f}万円 / "
                    f"買付額 {holding.purchase_amount:,.1f}万円"
                )

        cached_balance_result = st.session_state.get("_asset_import_balance")
        if cached_balance_result is not None and cached_balance_result.by_fund:
            st.markdown("**保有ファンドのバランス評価**")

            b1, b2 = st.columns(2)
            with b1:
                st.caption("カテゴリ別配分")
                for slice_ in cached_balance_result.by_category:
                    st.write(f"- {slice_.label}：{slice_.weight_pct:.1f}%")
            with b2:
                st.caption("口座種別の配分")
                for slice_ in cached_balance_result.by_account_type:
                    st.write(f"- {slice_.label}：{slice_.weight_pct:.1f}%")

            for warning in cached_balance_result.concentration_warnings:
                st.warning(warning)

            cached_commentary = st.session_state.get("_asset_import_commentary")
            if cached_commentary:
                with st.expander("📋 保有ファンドのバランス総評を見る", expanded=True):
                    st.markdown(cached_commentary)
                    st.caption(
                        "※配分の事実に基づく解説であり、売買を推奨するものでは"
                        "ありません。最終判断はご自身で行ってください。"
                    )

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
    auto_market_result = None
    try:
        auto_market_result = _cached_fetch_market_condition()
    except MarketDataError:
        auto_market_result = None

    condition_options = ["通常", "弱気相場", "暴落", "深刻な暴落"]
    default_index = (
        condition_options.index(auto_market_result.condition)
        if auto_market_result is not None
        else 0
    )

    market_condition = st.selectbox(
        "現在の市場環境",
        condition_options,
        index=default_index,
        help=(
            "S&P500の過去最高値からの下落率をもとに自動で初期値を提案します"
            "（取得できない場合は「通常」を初期値とします）。"
            "手動でいつでも変更できます。"
        ),
    )

    if auto_market_result is not None:
        st.caption(
            f"自動判定：S&P500は過去最高値（{auto_market_result.all_time_high:,.0f}）から"
            f"{auto_market_result.drawdown_pct * 100:.1f}%下落しており、"
            f"「{auto_market_result.condition}」を提案しています"
            "（手動で変更可能です）。"
        )
    else:
        st.caption(
            "市場データの自動取得に失敗したため、手動で選択してください。"
        )

st.subheader("3.5. 今月以降の大型支出予定")

st.caption(
    "旅行・車・医療などの不定期な大型支出を登録できます。"
    "今月分の予定は、今月のFIRE判定・取り崩しプランに反映されます。"
    "複数か月に分けて計上したい場合は「分散月数」を1より大きくしてください"
    "（例: 90万円を3か月に分散すると毎月30万円ずつ計上されます）。"
)

with st.form("add_large_expense_form", clear_on_submit=True):
    e1, e2, e3, e4, e5 = st.columns([2, 1, 1, 1, 1])

    with e1:
        expense_name = st.text_input("支出の名称", placeholder="例: 沖縄旅行")

    with e2:
        expense_category = st.selectbox("カテゴリ", LARGE_EXPENSE_CATEGORIES)

    with e3:
        expense_amount = st.number_input(
            "金額（万円）",
            min_value=0.0,
            value=0.0,
            step=1.0,
        )

    with e4:
        expense_month = st.text_input(
            "予定月（YYYY-MM）",
            value=date.today().strftime("%Y-%m"),
            help="分散する場合は、この月が分散区間の開始月になります。",
        )

    with e5:
        expense_distribution_months = st.number_input(
            "分散月数",
            min_value=1,
            max_value=36,
            value=1,
            step=1,
            help=(
                "1のままだと従来通り予定月に全額計上します。"
                "2以上にすると、予定月から連続する月に均等分散します"
                "（端数はできるだけ均等に各月へ配分されます）。"
            ),
        )

    expense_memo = st.text_input("メモ（任意）", placeholder="任意で入力")

    if st.form_submit_button("➕ 大型支出予定を追加"):
        try:
            add_large_expense(
                expense_name,
                expense_category,
                expense_amount,
                expense_month,
                memo=expense_memo,
                distribution_months=int(expense_distribution_months),
                path=LARGE_EXPENSE_PATH,
            )
        except ValueError as error:
            st.warning(str(error))
        else:
            _safe_log_event(
                "large_expense_added",
                f"大型支出予定を追加しました（カテゴリ: {expense_category}）。",
            )
            st.rerun()

large_expenses = load_large_expenses(path=LARGE_EXPENSE_PATH)

if large_expenses:
    st.caption(f"登録済みの大型支出予定：{len(large_expenses)}件")

    for index, expense in enumerate(large_expenses):
        expense_id = expense.get("id", "")

        with st.container(border=True):
            le1, le2 = st.columns([4, 1])

            with le1:
                distribution_months = int(expense.get("distribution_months", 1) or 1)

                if distribution_months > 1:
                    end_month = distribution_end_month(expense)
                    monthly_amount = expense.get("amount", 0) / distribution_months
                    st.write(
                        f"**{expense.get('expected_month', '---')}〜{end_month}　"
                        f"{expense.get('name', '')}"
                        f"（{expense.get('category', '')}）：合計"
                        f"{expense.get('amount', 0):,.1f}万円"
                        f"（{distribution_months}か月に分散・月あたり約"
                        f"{monthly_amount:,.1f}万円）**"
                    )
                else:
                    st.write(
                        f"**{expense.get('expected_month', '---')}　"
                        f"{expense.get('name', '')}"
                        f"（{expense.get('category', '')}）："
                        f"{expense.get('amount', 0):,.1f}万円**"
                    )

                if expense.get("memo"):
                    st.caption(expense["memo"])

            with le2:
                if st.button(
                    "🗑️ 削除",
                    key=f"delete_large_expense_{expense_id}_{index}",
                    use_container_width=True,
                ):
                    delete_large_expense(expense_id, path=LARGE_EXPENSE_PATH)
                    _safe_log_event(
                        "large_expense_deleted",
                        "大型支出予定を1件削除しました。",
                    )
                    st.rerun()
else:
    st.caption("登録済みの大型支出予定はありません。")

st.subheader("3.6. 年金受給開始年齢（ステージ判定用）")

st.caption(
    "60歳〜受給開始前／受給開始〜74歳／75歳以降のステージを判定し、"
    "今月の安全生活費の算出に反映します。詳細な年金額・NISA・iDeCoの"
    "設定はシミュレーション実行後の「8. NISA・iDeCo・年金最適化」で行います。"
)

pension_start_age = st.number_input(
    "年金受給開始年齢",
    min_value=65,
    max_value=75,
    value=65,
    step=1,
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

    current_month = date.today().strftime("%Y-%m")
    this_month_large_expense_total = total_for_month(
        load_large_expenses(path=LARGE_EXPENSE_PATH),
        current_month,
    )

    sequence_risk_result = calculate_sequence_risk_factor(
        current_age=current_age,
        pension_start_age=pension_start_age,
        total_assets=current_assets,
        annual_spending=annual_spending,
        annual_side_income=annual_side_income,
        expected_return_pct=expected_return,
        inflation_pct=inflation,
    )

    monthly_budget = calculate_monthly_budget(
        fire_result=result,
        action_result=base_action,
        market_crash=market_condition in ("暴落", "深刻な暴落"),
        upcoming_large_expense=this_month_large_expense_total,
        current_age=current_age,
        pension_start_age=pension_start_age,
        sequence_risk_factor=sequence_risk_result.risk_factor,
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

    st.subheader("4. 今月のFIRE判定")

    status_label = {
        "green": "🟢 安全",
        "yellow": "🟡 注意",
        "red": "🔴 警戒",
    }[monthly_budget.status]

    status_display = {
        "green": st.success,
        "yellow": st.warning,
        "red": st.error,
    }[monthly_budget.status]

    status_display(f"**{status_label}**")

    b1, b2, b3 = st.columns(3)

    b1.metric(
        "安全生活費",
        f"{monthly_budget.safe_monthly:,.1f}万円",
    )

    b2.metric(
        "推奨生活費",
        f"{monthly_budget.recommended_monthly:,.1f}万円",
    )

    b3.metric(
        "上限生活費",
        f"{monthly_budget.max_monthly:,.1f}万円",
    )

    st.caption(
        "安全生活費はこの範囲なら計画から外れにくい目安、"
        "上限生活費は資産・現金に余裕がある場合のみ使ってよい目安です。"
        "悲観ケースで資産が枯渇する見込み、または現金バッファ不足、"
        "市場暴落時は自動的に安全側に調整されます。"
    )

    if "early_retirement_stage" in monthly_budget.reasons:
        st.caption(
            "60歳〜年金受給開始前の期間は、シーケンス・オブ・リターンズ・"
            "リスク（早期に相場が下落した場合の影響の大きさ）を踏まえた"
            "調整を行っています。詳しくは下の「判定の根拠」をご覧ください。"
        )

    budget_explanation = build_budget_explanation(
        monthly_budget.reasons, monthly_budget.binding_safe_factor_reason
    )

    with st.expander("📋 この判定の根拠を見る"):
        st.write(f"**{budget_explanation.binding_summary}**")
        for detail in budget_explanation.details:
            st.write(f"- {detail}")

    record_monthly_judgment(
        current_month,
        safe_monthly=monthly_budget.safe_monthly,
        recommended_monthly=monthly_budget.recommended_monthly,
        max_monthly=monthly_budget.max_monthly,
        status=monthly_budget.status,
        binding_safe_factor_reason=monthly_budget.binding_safe_factor_reason,
        path=JUDGMENT_TREND_PATH,
    )

    st.subheader("4.5. 今月のFIRE判定の推移")

    judgment_trend_records = load_judgment_trend(path=JUDGMENT_TREND_PATH)

    if len(judgment_trend_records) >= 2:
        trend_df = pd.DataFrame(judgment_trend_records).set_index("month")[
            ["safe_monthly", "recommended_monthly", "max_monthly"]
        ]
        trend_df.columns = ["安全生活費", "推奨生活費", "上限生活費"]

        st.line_chart(trend_df, use_container_width=True)

        trend_status_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
        st.caption(
            "ガードレール状態の推移： "
            + "　".join(
                f"{record['month']}{trend_status_emoji.get(record['status'], '')}"
                for record in judgment_trend_records
            )
        )
    else:
        st.caption(
            "記録された月が2か月未満のため、推移グラフはまだ表示できません。"
            "シミュレーションを実行するたびに、今月の判定が自動的に記録されます"
            "（同じ月内に複数回実行した場合は最新の結果で上書きされます）。"
        )

    st.subheader("5. 今月の推奨行動")

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
        "市場環境に応じて現金バッファ・生活費・追加投資ルールを調整します。"
        "総資産シミュレーションそのものには二重計上しません。"
    )

    st.subheader("6. 市場環境別の防御ルール")

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

    st.subheader("7. AI FIREアドバイス")

    ai_advice = generate_ai_advice(
        fire_result=result,
        market_condition=market_condition,
        strategy=strategy,
        recommended_action=recommended_action,
        additional_investment=additional_investment,
        investment_withdrawal=investment_withdrawal,
    )

    st.markdown(ai_advice)
    st.subheader("8. NISA・iDeCo・年金最適化")

    t1, t2, t3 = st.columns(3)

    with t1:
        nisa_assets = st.number_input(
            "NISA現在残高（万円）",
            min_value=0.0,
            value=0.0,
            step=10.0,
            key="nisa_assets",
        )
        nisa_contributed = st.number_input(
            "NISA累計投資額・簿価（万円）",
            min_value=0.0,
            value=0.0,
            step=10.0,
            help="NISAの非課税保有限度額は取得価額（簿価）ベースです。",
            key="nisa_contributed",
        )
        nisa_growth_contributed = st.number_input(
            "うち成長投資枠の累計投資額（万円）",
            min_value=0.0,
            value=0.0,
            step=10.0,
            key="nisa_growth_contributed",
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
            key="taxable_assets",
        )
        taxable_gain_ratio_pct = st.slider(
            "課税口座の含み益割合（%）",
            min_value=0,
            max_value=100,
            value=30,
            step=5,
            help=(
                "課税口座残高のうち含み益（購入時より値上がりした部分）の"
                "割合の目安です。今月の取り崩しプランで、課税口座から売却"
                "する場合の税金の目安計算に使用します。"
            ),
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
        st.caption(
            f"年金受給開始年齢: **{pension_start_age}歳**"
            "（「3.6. 年金受給開始年齢」で設定した値を使用します）"
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

    st.subheader("9. 今月の取り崩しプラン")

    withdrawal_amount_needed = round(
        monthly_budget.safe_monthly + this_month_large_expense_total, 2
    )

    withdrawal_plan = calculate_withdrawal_plan(
        amount_needed=withdrawal_amount_needed,
        cash_assets=cash_assets,
        cash_buffer_target=target_cash,
        taxable_assets=taxable_assets,
        nisa_assets=nisa_assets,
        ideco_assets=ideco_assets,
        current_age=current_age,
        ideco_access_age=tax_result.ideco_access_age,
        pension_start_age=tax_result.pension_start_age,
        pension_monthly_income=tax_result.pension_monthly_income,
        taxable_gain_ratio=taxable_gain_ratio_pct / 100.0,
    )

    if this_month_large_expense_total > 0.005:
        st.caption(
            f"今月の安全生活費 {monthly_budget.safe_monthly:,.1f}万円に、"
            f"今月予定の大型支出 {this_month_large_expense_total:,.1f}万円を加えた"
            f"合計 {withdrawal_amount_needed:,.1f}万円を、どこから充当するかの候補です。"
        )
    else:
        st.caption(
            f"今月の安全生活費 {monthly_budget.safe_monthly:,.1f}万円を、"
            "どこから充当するかの候補です。"
        )

    for step in withdrawal_plan.steps:
        if step.amount > 0:
            st.write(f"**{step.source}：{step.amount:,.1f}万円** — {step.reason}")
        else:
            st.caption(f"{step.source} — {step.reason}")

    if withdrawal_plan.total_estimated_tax > 0.005:
        st.caption(
            f"今回のプランに含まれる課税口座の取り崩しにかかる税金の目安は"
            f"合計{withdrawal_plan.total_estimated_tax:,.1f}万円です"
            "（簡易的な目安であり、実際の税額とは異なる場合があります）。"
        )

    if withdrawal_plan.dipped_into_cash_buffer:
        st.warning(
            "最低現金バッファを一時的に下回る取り崩し案です。"
            "早めにバッファの補充を検討してください。"
        )

    if withdrawal_plan.shortfall_uncovered > 0.005:
        st.error(
            f"現金・課税口座・NISA・iDeCo・年金では"
            f"{withdrawal_plan.shortfall_uncovered:,.1f}万円が不足しています。"
            "生活費の見直しが必要な水準です。"
        )

    _safe_log_event(
        "simulation_executed",
        f"FIREシミュレーションを実行しました（市場環境: {market_condition}）。",
    )

    st.session_state["latest_simulation"] = {
        "name": "FIREシミュレーション",
        "inputs": {
            "current_age": current_age,
            "end_age": end_age,
            "current_assets": current_assets,
            "cash_assets": cash_assets,
            "annual_spending": annual_spending,
            "annual_side_income": annual_side_income,
            "expected_return": expected_return,
            "inflation": inflation,
            "safety_margin": safety_margin,
            "min_cash_months": min_cash_months,
            "market_condition": market_condition,
            "nisa_assets": nisa_assets,
            "nisa_contributed": nisa_contributed,
            "nisa_growth_contributed": nisa_growth_contributed,
            "nisa_annual_contributed": nisa_annual_contributed,
            "taxable_assets": taxable_assets,
            "ideco_assets": ideco_assets,
            "ideco_monthly_contribution": ideco_monthly_contribution,
            "ideco_annual_limit": ideco_annual_limit,
            "annual_pension": annual_pension,
            "pension_start_age": pension_start_age,
        },
        "results": {
            "asset_depletion_label": result.asset_depletion_label,
            "net_annual_spending": result.net_annual_spending,
            "recommended_monthly_spending": result.recommended_monthly_spending,
            "cash_months": result.cash_months,
            "target_cash": target_cash,
            "additional_investment": additional_investment,
            "investment_withdrawal": investment_withdrawal,
            "recommended_action": recommended_action,
            "pension_gap_after_start": tax_result.pension_gap_after_start,
            "nisa_remaining_limit": tax_result.nisa_remaining_limit,
            "nisa_growth_remaining_limit": tax_result.nisa_growth_remaining_limit,
            "nisa_annual_room": tax_result.nisa_annual_room,
            "ideco_annual_contribution": tax_result.ideco_annual_contribution,
        },
        "scenarios": [
            {
                "name": scenario.name,
                "final_assets": scenario.final_assets,
                "min_assets": scenario.min_assets,
                "depleted_at": scenario.depleted_at,
            }
            for scenario in result.scenario_summaries
        ],
    }


    st.subheader("10. 現在のFIRE状態")

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

    st.subheader("11. 資産推移")

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

    st.subheader("12. シナリオ結果")

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
st.subheader("13. 保存・履歴管理")

latest_simulation = st.session_state.get(
    "latest_simulation"
)

if latest_simulation:
    st.write(
        "直前のシミュレーション結果を名前を付けて保存できます。"
    )

    history_name = st.text_input(
        "履歴名",
        value=latest_simulation.get(
            "name",
            "FIREシミュレーション",
        ),
        key="history_name",
    )

    if st.button(
        "💾 最新結果を履歴に保存",
        use_container_width=True,
    ):
        record = dict(latest_simulation)
        record["name"] = history_name.strip() or "FIREシミュレーション"

        save_history(
            record,
            path=HISTORY_PATH,
        )

        _safe_log_event(
            "history_saved",
            f"シミュレーション結果を履歴に保存しました（名称: {record['name']}）。",
        )

        st.success(
            f"「{record['name']}」を履歴に保存しました。"
        )
        st.rerun()
else:
    st.info(
        "「FIREシミュレーションを実行」を先に実行すると、"
        "ここから結果を保存できます。"
    )

history_records = load_history(
    path=HISTORY_PATH,
)

if history_records:
    st.markdown("### 保存済み履歴")

    st.caption(
        f"最大20件まで保存されます。現在 {len(history_records)} 件。"
    )

    history_keyword_filter = st.text_input(
        "履歴名で検索",
        value="",
        placeholder="例: 楽観シナリオ",
        key="history_keyword_filter",
    )

    history_date_col1, history_date_col2 = st.columns(2)
    with history_date_col1:
        history_start_date = st.date_input(
            "作成日（開始・この日を含む）",
            value=None,
            key="history_start_date",
        )
    with history_date_col2:
        history_end_date = st.date_input(
            "作成日（終了・この日を含む）",
            value=None,
            key="history_end_date",
        )

    filtered_history_records = filter_history(
        history_records,
        keyword=history_keyword_filter,
        start_date=str(history_start_date) if history_start_date else None,
        end_date=str(history_end_date) if history_end_date else None,
    )

    st.caption(f"絞り込み後の件数: {len(filtered_history_records)}件")

    if not filtered_history_records:
        st.info("条件に一致する履歴はありません。")

    for index, record in enumerate(filtered_history_records):
        record_id = record.get("id", "")
        results = record.get("results", {})

        with st.container(border=True):
            c1, c2 = st.columns([4, 1])

            with c1:
                st.markdown(
                    f"**{record.get('name', '名称未設定')}**"
                )

                st.caption(
                    record.get(
                        "created_at",
                        "日時不明",
                    )
                )

                st.write(
                    f"資産寿命判定: "
                    f"**{results.get('asset_depletion_label', '---')}**"
                )

                st.write(
                    f"純年間支出: "
                    f"**{results.get('net_annual_spending', 0):,.0f}万円**"
                )

                st.write(
                    f"現金: "
                    f"**{results.get('cash_months', 0):,.1f}か月**"
                )

                rename_col1, rename_col2 = st.columns([3, 1])

                with rename_col1:
                    new_name = st.text_input(
                        "名称を変更",
                        value=record.get("name", "名称未設定"),
                        key=f"rename_history_input_{record_id}_{index}",
                        label_visibility="collapsed",
                    )

                with rename_col2:
                    if st.button(
                        "✏️ 名称変更",
                        key=f"rename_history_{record_id}_{index}",
                        use_container_width=True,
                    ):
                        try:
                            renamed = rename_history(
                                record_id,
                                new_name,
                                path=HISTORY_PATH,
                            )
                        except ValueError as error:
                            st.warning(str(error))
                        else:
                            if renamed:
                                _safe_log_event(
                                    "history_renamed",
                                    "履歴の名称を変更しました。",
                                )
                                st.rerun()
                            else:
                                st.warning(
                                    "対象の履歴が見つかりませんでした。"
                                )

            with c2:
                if st.button(
                    "🗑️ 削除",
                    key=f"delete_history_{record_id}_{index}",
                ):
                    delete_history(
                        record_id,
                        path=HISTORY_PATH,
                    )
                    _safe_log_event(
                        "history_deleted",
                        "履歴を1件削除しました。",
                    )
                    st.rerun()

    st.markdown("### 履歴のエクスポート")

    st.caption(
        "検索・期間で絞り込んだ結果をCSVでダウンロードできます"
        "（絞り込みが未入力の場合は全件が対象です）。"
        "20件の上限で古い履歴が消える前の保管用途にもご利用いただけます。"
    )

    st.download_button(
        label="📥 保存済み履歴をCSVでダウンロード",
        data=export_history_to_csv(filtered_history_records),
        file_name=history_export_filename(),
        mime="text/csv",
        use_container_width=True,
        disabled=not filtered_history_records,
    )

    if st.button(
        "🗑️ 全履歴を削除",
        use_container_width=True,
    ):
        clear_history(path=HISTORY_PATH)
        _safe_log_event(
            "history_cleared",
            "保存済みの履歴をすべて削除しました。",
        )
        st.rerun()
else:
    st.info("保存済み履歴はありません。")