from dataclasses import dataclass, field
from typing import List, Optional

# 上場株式等の譲渡益に対する税率（所得税15%＋復興特別所得税0.315%＋
# 住民税5%）。Sprint 23で追加。課税口座からの取り崩しにのみ適用する
# （NISAは非課税、iDeCoは受取時課税の仕組みが大きく異なるため対象外）。
TAXABLE_CAPITAL_GAINS_TAX_RATE = 0.20315


@dataclass
class WithdrawalStep:
    source: str
    amount: float
    reason: str
    # Sprint 23で追加。課税口座ステップのみ値が入る参考情報で、
    # amountの意味（今月の資金繰りに充当する純額）自体は変更しない。
    estimated_tax: float = 0.0
    gross_sell_amount: Optional[float] = None


@dataclass
class WithdrawalPlanResult:
    steps: List[WithdrawalStep] = field(default_factory=list)
    total_covered: float = 0.0
    shortfall_uncovered: float = 0.0
    dipped_into_cash_buffer: bool = False
    total_estimated_tax: float = 0.0


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
    taxable_gain_ratio: float = 0.0,
) -> WithdrawalPlanResult:
    """今月必要な金額を、どの資産・口座から取り崩すか判定する。

    優先順位: 現金バッファ内の現金 → 受給中の年金 → 課税口座 →
    NISA → iDeCo（60歳以上のみ） → 現金バッファを下回っての取り崩し（最終手段）。

    課税口座をNISAより先にするのは、NISAの非課税運用をできるだけ
    長く維持するため。iDeCoは原則60歳まで引き出せないため、
    current_age >= ideco_access_ageの場合のみ候補に入れる。

    このエンジンはfire_engine / action_engine / tax_optimizationの
    計算結果を組み合わせるだけで、それぞれの計算ロジックには手を加えない。

    taxable_gain_ratio（Sprint 23で追加、省略可能・デフォルト0.0）は
    課税口座残高に占める含み益の割合（0.0〜1.0）。課税口座ステップの
    amount（＝今月の資金繰りに充当する純額）自体はこれまで通り変更せず、
    参考情報として次の2つを追加で算出する：
    - estimated_tax: このステップのamountに含み益割合と税率をかけた
      推定税額の目安（amount * taxable_gain_ratio * 税率）
    - gross_sell_amount: 上記税額を踏まえた、実際に売却する額の目安
      （amount + estimated_tax）
    いずれも簡易的な目安であり、実際の確定申告・税額計算に代わるもの
    ではない。0.0（デフォルト）の場合は既存呼び出しと完全に同じ挙動になる。
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

    if not (0.0 <= taxable_gain_ratio <= 1.0):
        raise ValueError("課税口座の含み益割合は0.0〜1.0の範囲で指定してください。")

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
        reason = "NISAの非課税運用を維持するため、課税口座から先に取り崩します。"

        estimated_tax = 0.0
        gross_sell_amount = None

        if taxable_gain_ratio > 0.0:
            estimated_tax = round(
                use * taxable_gain_ratio * TAXABLE_CAPITAL_GAINS_TAX_RATE, 2
            )
            gross_sell_amount = round(use + estimated_tax, 2)
            reason += (
                f" 含み益割合を{taxable_gain_ratio * 100:.0f}%と仮定すると、"
                f"税金の目安は{estimated_tax:,.1f}万円、"
                f"実際に売却する額の目安は{gross_sell_amount:,.1f}万円です。"
                "（簡易的な目安であり、実際の税額とは異なる場合があります）"
            )

        steps.append(
            WithdrawalStep(
                source="課税口座",
                amount=round(use, 2),
                reason=reason,
                estimated_tax=estimated_tax,
                gross_sell_amount=gross_sell_amount,
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
    total_estimated_tax = round(sum(step.estimated_tax for step in steps), 2)

    return WithdrawalPlanResult(
        steps=steps,
        total_covered=total_covered,
        shortfall_uncovered=round(max(remaining, 0.0), 2),
        dipped_into_cash_buffer=dipped_into_cash_buffer,
        total_estimated_tax=total_estimated_tax,
    )

