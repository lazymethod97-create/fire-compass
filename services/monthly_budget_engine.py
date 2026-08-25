from dataclasses import dataclass
from typing import List

from services.fire_engine import FireResult
from services.action_engine import ActionResult


@dataclass
class MonthlyBudgetResult:
    safe_monthly: float
    recommended_monthly: float
    max_monthly: float
    status: str  # "green" | "yellow" | "red"
    reasons: List[str]


# 係数はここに集約する。数値の意味づけ（何%下げるか等）は
# 今後のレビューで調整しやすいよう、関数ロジックとは分離している。
_SAFE_FACTOR_HEALTHY = 1.00
_SAFE_FACTOR_SHORTAGE = 0.85
_SAFE_FACTOR_BEAR_DEPLETES = 0.70
_SAFE_FACTOR_CRASH = 0.60

_MAX_FACTOR_HEALTHY = 1.15
_MAX_FACTOR_NEUTRAL = 1.00


def calculate_monthly_budget(
    fire_result: FireResult,
    action_result: ActionResult,
    market_crash: bool = False,
    upcoming_large_expense: float = 0.0,
) -> MonthlyBudgetResult:
    """run_fire_simulationとcalculate_monthly_actionの出力から、
    今月の安全生活費・推奨生活費・上限生活費とガードレール判定を算出する。

    この関数は既存2エンジンの出力のみを使用する合成ロジックであり、
    資産寿命シミュレーションや現金バッファ計算そのものには手を加えない。

    market_crashは暴落検知機能が実装されるまでの暫定引数。
    将来のSprintで市場データと連動させる想定。

    upcoming_large_expenseは今月に予定されている大型支出（旅行・車・医療等）
    の合計額（万円）。デフォルト0.0は既存呼び出しと完全に同じ挙動になる。
    安全/推奨/上限生活費の金額そのものは変更せず、現金の余力（cash_surplus）
    を超える予定支出がある場合にのみガードレール判定を1段階厳しくする
    （green→yellowへの格下げのみ。既にyellow/redの場合はそのまま）。
    """
    if upcoming_large_expense < 0:
        raise ValueError("大型支出予定の合計額は0以上にしてください。")

    recommended_monthly = fire_result.recommended_monthly_spending
    reasons: List[str] = []

    bear_summary = next(
        (s for s in fire_result.scenario_summaries if s.name == "悲観ケース"),
        None,
    )
    bear_depletes = (
        bear_summary is not None and bear_summary.depleted_at != "期間内に枯渇せず"
    )

    cash_shortage_ratio = (
        action_result.cash_shortage / action_result.target_cash_amount
        if action_result.target_cash_amount > 0
        else 0.0
    )

    # --- 安全生活費の係数 ---
    if market_crash:
        safe_factor = _SAFE_FACTOR_CRASH
        reasons.append("market_crash_active")
    elif bear_depletes:
        safe_factor = _SAFE_FACTOR_BEAR_DEPLETES
        reasons.append("bear_case_depletes")
    elif cash_shortage_ratio > 0.0:
        safe_factor = _SAFE_FACTOR_SHORTAGE
        reasons.append("cash_buffer_below_target")
    else:
        safe_factor = _SAFE_FACTOR_HEALTHY
        reasons.append("cash_buffer_healthy")

    safe_monthly = round(recommended_monthly * safe_factor, 2)

    # --- 上限生活費の係数（余裕がある時だけ推奨より高くする） ---
    if market_crash or bear_depletes or cash_shortage_ratio > 0.0:
        max_factor = _MAX_FACTOR_NEUTRAL
    else:
        max_factor = _MAX_FACTOR_HEALTHY
        reasons.append("upside_allowed")

    max_monthly = round(recommended_monthly * max_factor, 2)

    # --- ガードレール判定 ---
    if market_crash or bear_depletes:
        status = "red"
    elif cash_shortage_ratio > 0.0:
        status = "yellow"
    else:
        status = "green"

    # --- 大型支出予定による格下げ（既存の判定を厳しくする方向にのみ働く） ---
    if upcoming_large_expense > 0.005:
        if upcoming_large_expense > action_result.cash_surplus + 0.005:
            reasons.append("large_expense_exceeds_cash_surplus")
            if status == "green":
                status = "yellow"
        else:
            reasons.append("large_expense_within_cash_surplus")

    return MonthlyBudgetResult(
        safe_monthly=safe_monthly,
        recommended_monthly=recommended_monthly,
        max_monthly=max_monthly,
        status=status,
        reasons=reasons,
    )
