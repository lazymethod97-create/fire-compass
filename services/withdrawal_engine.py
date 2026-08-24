from dataclasses import dataclass, field
from typing import List


@dataclass
class WithdrawalStep:
    source: str
    amount: float
    reason: str


@dataclass
class WithdrawalPlanResult:
    steps: List[WithdrawalStep] = field(default_factory=list)
    total_covered: float = 0.0
    shortfall_uncovered: float = 0.0
    dipped_into_cash_buffer: bool = False


def calculate_withdrawal_plan(
    amount_needed: float,
    cash_assets: float,
    cash_buffer_target: float,
    taxable_assets: float,
    nisa_assets: float,
    ideco_assets: float,
    current_age: int,
    ideco_access_age: int,
    pension_start_age: int,
    pension_monthly_income: float,
) -> WithdrawalPlanResult:
    """今月必要な金額を、どの資産・口座から取り崩すか判定する。

    優先順位: 現金バッファ内の現金 → 受給中の年金 → 課税口座 →
    NISA → iDeCo（60歳以上のみ） → 現金バッファを下回っての取り崩し（最終手段）。

    課税口座をNISAより先にするのは、NISAの非課税運用をできるだけ
    長く維持するため。iDeCoは原則60歳まで引き出せないため、
    current_age >= ideco_access_ageの場合のみ候補に入れる。

    このエンジンはfire_engine / action_engine / tax_optimizationの
    計算結果を組み合わせるだけで、それぞれの計算ロジックには手を加えない。
    """
    numeric_values = (
        amount_needed,
        cash_assets,
        cash_buffer_target,
        taxable_assets,
        nisa_assets,
        ideco_assets,
        pension_monthly_income,
    )
    if any(value < 0 for value in numeric_values):
        raise ValueError("金額はすべて0以上にしてください。")

    remaining = amount_needed
    steps: List[WithdrawalStep] = []

    # 1. 現金バッファ内の現金
    available_cash = max(cash_assets - cash_buffer_target, 0.0)
    if remaining > 0.005 and available_cash > 0.005:
        use = min(available_cash, remaining)
        steps.append(
            WithdrawalStep(
                source="現金",
                amount=round(use, 2),
                reason="現金バッファの範囲内なので、まず現金から充当します。",
            )
        )
        remaining -= use

    # 2. 受給中の年金
    if remaining > 0.005 and current_age >= pension_start_age and pension_monthly_income > 0.005:
        use = min(pension_monthly_income, remaining)
        steps.append(
            WithdrawalStep(
                source="年金",
                amount=round(use, 2),
                reason="年金受給中のため、不足分にまず年金収入を充当します。",
            )
        )
        remaining -= use

    # 3. 課税口座
    if remaining > 0.005 and taxable_assets > 0.005:
        use = min(taxable_assets, remaining)
        steps.append(
            WithdrawalStep(
                source="課税口座",
                amount=round(use, 2),
                reason="NISAの非課税運用を維持するため、課税口座から先に取り崩します。",
            )
        )
        remaining -= use

    # 4. NISA
    if remaining > 0.005 and nisa_assets > 0.005:
        use = min(nisa_assets, remaining)
        steps.append(
            WithdrawalStep(
                source="NISA",
                amount=round(use, 2),
                reason="課税口座だけでは不足するため、NISAから取り崩します。",
            )
        )
        remaining -= use

    # 5. iDeCo（引き出し可能年齢以上のみ）
    if remaining > 0.005 and ideco_assets > 0.005:
        if current_age >= ideco_access_age:
            use = min(ideco_assets, remaining)
            steps.append(
                WithdrawalStep(
                    source="iDeCo",
                    amount=round(use, 2),
                    reason="他の資産では不足するため、iDeCoから取り崩します。",
                )
            )
            remaining -= use
        else:
            steps.append(
                WithdrawalStep(
                    source="iDeCo（利用不可）",
                    amount=0.0,
                    reason=(
                        f"iDeCoは{ideco_access_age}歳まで引き出せないため、"
                        "候補から除外しました。"
                    ),
                )
            )

    dipped_into_cash_buffer = False

    # 6. 最終手段：現金バッファを下回っての取り崩し
    if remaining > 0.005:
        buffer_cash = min(cash_buffer_target, cash_assets) - available_cash
        buffer_cash = max(buffer_cash, 0.0)
        if buffer_cash > 0.005:
            use = min(buffer_cash, remaining)
            steps.append(
                WithdrawalStep(
                    source="現金（バッファ割れ）",
                    amount=round(use, 2),
                    reason=(
                        "他のすべての資産では不足するため、"
                        "最低現金バッファを一時的に下回って充当します。"
                        "早めにバッファの補充を検討してください。"
                    ),
                )
            )
            remaining -= use
            dipped_into_cash_buffer = True

    total_covered = round(amount_needed - remaining, 2)

    return WithdrawalPlanResult(
        steps=steps,
        total_covered=total_covered,
        shortfall_uncovered=round(max(remaining, 0.0), 2),
        dipped_into_cash_buffer=dipped_into_cash_buffer,
    )
