from dataclasses import dataclass


@dataclass
class ActionResult:
    target_cash_amount: float
    target_cash_months: float
    cash_surplus: float
    cash_shortage: float
    additional_investment: float
    investment_withdrawal: float
    action: str
    reason: str


def calculate_monthly_action(
    cash_assets: float,
    total_assets: float,
    net_annual_spending: float,
    min_cash_months: float = 12.0,
) -> ActionResult:
    """現金バッファを基準に、追加投資または投資資産からの補充額を計算する。

    金額単位はすべて万円。これは現金と投資資産の配分を示すルールであり、
    総金融資産そのものを増減させる計算ではない。
    """
    if cash_assets < 0:
        raise ValueError("現金・預金は0以上にしてください。")
    if total_assets < 0:
        raise ValueError("総金融資産は0以上にしてください。")
    if cash_assets > total_assets:
        raise ValueError("現金・預金は総金融資産以下にしてください。")
    if net_annual_spending < 0:
        raise ValueError("純年間支出は0以上にしてください。")
    if min_cash_months < 0:
        raise ValueError("最低現金バッファは0か月以上にしてください。")

    net_monthly_spending = net_annual_spending / 12.0
    target_cash = net_monthly_spending * min_cash_months
    cash_surplus = max(cash_assets - target_cash, 0.0)
    cash_shortage = max(target_cash - cash_assets, 0.0)
    investment_assets = max(total_assets - cash_assets, 0.0)

    if cash_surplus > 0.005:
        additional_investment = cash_surplus
        investment_withdrawal = 0.0
        action = "追加投資"
        reason = (
            f"現金が目標の{min_cash_months:.1f}か月分を上回っているため、"
            f"超過分{additional_investment:,.1f}万円を追加投資候補とします。"
        )
    elif cash_shortage > 0.005:
        additional_investment = 0.0
        investment_withdrawal = min(cash_shortage, investment_assets)
        if investment_withdrawal > 0.005:
            action = "投資信託を取り崩して現金を補充"
            reason = (
                f"現金が目標の{min_cash_months:.1f}か月分を下回っているため、"
                f"不足分{investment_withdrawal:,.1f}万円を投資資産から補充する候補とします。"
            )
        else:
            action = "現金バッファ不足"
            reason = (
                "現金バッファが不足していますが、投資資産残高がないため、"
                "投資信託からの補充は計算できません。"
            )
    else:
        additional_investment = 0.0
        investment_withdrawal = 0.0
        action = "取り崩し・追加投資は不要"
        reason = (
            f"現金が目標の{min_cash_months:.1f}か月分とほぼ一致しているため、"
            "今月の資産配分変更は不要と判断します。"
        )

    return ActionResult(
        target_cash_amount=target_cash,
        target_cash_months=min_cash_months,
        cash_surplus=cash_surplus,
        cash_shortage=cash_shortage,
        additional_investment=additional_investment,
        investment_withdrawal=investment_withdrawal,
        action=action,
        reason=reason,
    )
