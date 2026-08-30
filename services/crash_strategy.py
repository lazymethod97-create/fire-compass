from dataclasses import dataclass

STRATEGIES = {
    "通常": {
        "buffer_add": 0.0,
        "investment_ratio": 1.0,
        "spending_reduction": 0.0,
        "label": "通常モード",
    },
    "弱気相場": {
        "buffer_add": 3.0,
        "investment_ratio": 0.5,
        "spending_reduction": 5.0,
        "label": "慎重モード",
    },
    "暴落": {
        "buffer_add": 6.0,
        "investment_ratio": 0.0,
        "spending_reduction": 10.0,
        "label": "防御モード",
    },
    "深刻な暴落": {
        "buffer_add": 12.0,
        "investment_ratio": 0.0,
        "spending_reduction": 15.0,
        "label": "強い防御モード",
    },
}


@dataclass(frozen=True)
class CrashStrategy:
    condition: str
    target_cash_months: float
    additional_investment_ratio: float
    spending_reduction_pct: float
    recommended_monthly_spending: float
    label: str
    reason: str


def calculate_crash_strategy(
    base_monthly_spending: float,
    min_cash_months: float,
    condition: str,
) -> CrashStrategy:
    if base_monthly_spending < 0:
        raise ValueError("基準月間生活費は0以上にしてください。")

    if min_cash_months < 0:
        raise ValueError("最低現金バッファは0か月以上にしてください。")

    if condition not in STRATEGIES:
        raise ValueError("未知の市場環境です。")

    cfg = STRATEGIES[condition]

    reduction = cfg["spending_reduction"]

    recommended_monthly = round(
        base_monthly_spending * (1 - reduction / 100),
        2,
    )

    if condition == "通常":
        reason = (
            "通常時なので、現金バッファ・生活費・追加投資は"
            "通常ルールをそのまま使用します。"
        )
    elif condition == "弱気相場":
        reason = (
            "弱気相場では追加投資を50%に抑え、"
            "生活費を5%抑え、"
            "現金バッファを3か月上乗せします。"
        )
    elif condition == "暴落":
        reason = (
            "暴落時は追加投資を停止し、"
            "生活費を10%抑え、"
            "現金バッファを6か月上乗せします。"
        )
    else:
        reason = (
            "深刻な暴落時は追加投資を停止し、"
            "生活費を15%抑え、"
            "現金バッファを12か月上乗せします。"
        )

    return CrashStrategy(
        condition=condition,
        target_cash_months=min_cash_months + cfg["buffer_add"],
        additional_investment_ratio=cfg["investment_ratio"],
        spending_reduction_pct=reduction,
        recommended_monthly_spending=recommended_monthly,
        label=cfg["label"],
        reason=reason,
    )
