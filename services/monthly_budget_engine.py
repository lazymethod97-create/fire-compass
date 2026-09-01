from dataclasses import dataclass
from typing import List, Optional

from services.fire_engine import FireResult
from services.action_engine import ActionResult


@dataclass
class MonthlyBudgetResult:
    safe_monthly: float
    recommended_monthly: float
    max_monthly: float
    status: str  # "green" | "yellow" | "red"
    reasons: List[str]
    # Sprint 24で追加。safe_monthlyの算出に最終的に採用された係数が
    # どの要因によるものかを示すタグ（reasons内のタグのいずれかと一致する）。
    # 表示層（services/budget_explanation.py）が「今、何が一番効いているか」
    # を説明するために参照する。計算結果そのものには影響しない。
    binding_safe_factor_reason: str = "cash_buffer_healthy"


# 係数はここに集約する。数値の意味づけ（何%下げるか等）は
# 今後のレビューで調整しやすいよう、関数ロジックとは分離している。
_SAFE_FACTOR_HEALTHY = 1.00
_SAFE_FACTOR_SHORTAGE = 0.85
_SAFE_FACTOR_BEAR_DEPLETES = 0.70
_SAFE_FACTOR_CRASH = 0.60

_MAX_FACTOR_HEALTHY = 1.15
_MAX_FACTOR_NEUTRAL = 1.00

# Sprint 21: 年金開始前後のステージ別安全生活費係数。
# 早期リタイア期（60歳〜年金受給開始前）はシーケンス・オブ・リターンズ・
# リスクが最も高い時期のため、後期（75歳以降）は保守的な生活費を優先する
# ため、それぞれ安全生活費をやや厳しめに算出する。
_SAFE_FACTOR_EARLY_RETIREMENT = 0.95
_SAFE_FACTOR_LATE_STAGE = 0.90

_EARLY_RETIREMENT_START_AGE = 60
_LATE_STAGE_START_AGE = 75


def _determine_life_stage(
    current_age: Optional[int],
    pension_start_age: Optional[int],
) -> Optional[str]:
    """年齢と年金受給開始年齢から、ステージ別調整の対象かどうかを判定する。

    current_age・pension_start_ageのいずれかが未指定の場合は判定不能として
    Noneを返す（ステージ調整は行わず、既存の挙動をそのまま維持する）。

    区分:
    - 60歳未満: 対象外（資産形成期。既存ロジックのまま）
    - 60歳以上・年金受給開始年齢未満: "early_retirement"（早期リタイア期）
    - 年金受給開始年齢以上・75歳未満: "receiving_pension"（受給期。既存の
      年金関連ロジックのみが働き、追加の安全係数は適用しない）
    - 75歳以上: "late_stage"（後期）
    """
    if current_age is None or pension_start_age is None:
        return None

    if current_age < _EARLY_RETIREMENT_START_AGE:
        return None

    if current_age < pension_start_age:
        return "early_retirement"

    if current_age < _LATE_STAGE_START_AGE:
        return "receiving_pension"

    return "late_stage"


def calculate_monthly_budget(
    fire_result: FireResult,
    action_result: ActionResult,
    market_crash: bool = False,
    upcoming_large_expense: float = 0.0,
    current_age: Optional[int] = None,
    pension_start_age: Optional[int] = None,
    sequence_risk_factor: Optional[float] = None,
    monthly_social_insurance: float = 0.0,
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

    current_age・pension_start_ageはSprint 21で追加されたステージ判定用の
    引数（いずれも省略可能）。どちらか一方でも省略した場合はステージ調整を
    行わず、既存呼び出しと完全に同じ挙動になる。
    早期リタイア期（60歳〜年金受給開始前）と後期（75歳以降）では、
    安全生活費の係数がより保守的な方向にのみ働く
    （市場暴落・悲観ケース枯渇・現金バッファ不足による既存の係数の方が
    厳しい場合は、その既存係数を優先し、ステージ係数で上書きしない）。
    上限生活費・ガードレール判定（green/yellow/red）自体はステージによって
    変化しない。

    sequence_risk_factorはSprint 22で追加された、シーケンス・オブ・
    リターンズ・リスク（services.sequence_risk_engine）の評価結果である
    係数（省略可能）。この関数自体はモンテカルロ計算を行わず、
    呼び出し側が算出した係数を受け取って他の係数と比較するだけである。
    早期リタイア期（life_stage == "early_retirement"）の場合にのみ、
    既存の安全係数より厳しい（低い）場合に限って適用する。それ以外の
    ステージでは無視する（sequence_risk_engine側でも早期リタイア期以外は
    1.00を返す設計だが、本関数側でも同じ条件で二重にガードする）。
    早期リタイア期で係数を受け取った場合はreasonsに
    "sequence_risk_evaluated"を追加し、実際にそれが既存係数より厳しく
    採用された場合のみ"sequence_risk_applied"も追加する
    （UI側で「系列リスクにより厳しめに算出した」旨を出し分けるため）。
    上限生活費・ガードレール判定（green/yellow/red）には影響しない。

    binding_safe_factor_reason（Sprint 24で追加）は、safe_monthlyの算出に
    最終的に採用された係数がどの要因によるものかを示すタグで、reasons内の
    いずれかのタグと一致する。services.budget_explanationが「今、何が
    一番効いているか」を説明する際に使用する。

    monthly_social_insurance（Sprint 30で追加、省略可能・デフォルト0.0）は、
    services.social_insurance_engineで算出した国民健康保険料・国民年金
    保険料の月額合計（万円）。FIRE後は給与天引きがなくなり自分で納付する
    必要がある固定費であるため、係数調整ではなく安全・推奨・上限生活費
    それぞれから直接差し引く（0円未満にはならないようフロア処理する）。
    デフォルト0.0の場合は既存呼び出しと完全に同じ挙動になる。
    ガードレール判定（green/yellow/red）自体はこの引数によって変化しない
    （他の格下げ要因と異なり、格下げ判定ではなく金額の直接控除のみを
    行う設計。既存のupcoming_large_expenseによるgreen→yellow格下げ判定は
    差し引き後の金額ではなく従来通りcash_surplusとの比較で行う）。
    """
    if upcoming_large_expense < 0:
        raise ValueError("大型支出予定の合計額は0以上にしてください。")

    if current_age is not None and current_age < 0:
        raise ValueError("現在年齢は0以上にしてください。")

    if pension_start_age is not None and pension_start_age < 0:
        raise ValueError("年金受給開始年齢は0以上にしてください。")

    if monthly_social_insurance < 0:
        raise ValueError("社会保険料の月額は0以上にしてください。")

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
        binding_reason = "market_crash_active"
    elif bear_depletes:
        safe_factor = _SAFE_FACTOR_BEAR_DEPLETES
        reasons.append("bear_case_depletes")
        binding_reason = "bear_case_depletes"
    elif cash_shortage_ratio > 0.0:
        safe_factor = _SAFE_FACTOR_SHORTAGE
        reasons.append("cash_buffer_below_target")
        binding_reason = "cash_buffer_below_target"
    else:
        safe_factor = _SAFE_FACTOR_HEALTHY
        reasons.append("cash_buffer_healthy")
        binding_reason = "cash_buffer_healthy"

    # --- ステージ別の安全生活費係数（Sprint 21） ---
    # より保守的な（低い）係数の場合にのみ上書きする。市場暴落・悲観ケース
    # 枯渇・現金バッファ不足のいずれかで既に安全係数が厳しくなっている場合は、
    # その既存係数をそのまま優先する。
    life_stage = _determine_life_stage(current_age, pension_start_age)

    if life_stage == "early_retirement":
        reasons.append("early_retirement_stage")
        if _SAFE_FACTOR_EARLY_RETIREMENT < safe_factor:
            safe_factor = _SAFE_FACTOR_EARLY_RETIREMENT
            binding_reason = "early_retirement_stage"
    elif life_stage == "late_stage":
        reasons.append("late_stage_conservative")
        if _SAFE_FACTOR_LATE_STAGE < safe_factor:
            safe_factor = _SAFE_FACTOR_LATE_STAGE
            binding_reason = "late_stage_conservative"

    # --- シーケンス・オブ・リターンズ・リスク係数（Sprint 22） ---
    # 早期リタイア期のみ、既存の安全係数より厳しい場合にのみ適用する。
    if (
        life_stage == "early_retirement"
        and sequence_risk_factor is not None
    ):
        reasons.append("sequence_risk_evaluated")
        if sequence_risk_factor < safe_factor:
            safe_factor = sequence_risk_factor
            reasons.append("sequence_risk_applied")
            binding_reason = "sequence_risk_applied"

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

    # --- 社会保険料（国保・国民年金）の直接控除（Sprint 30） ---
    # 係数調整ではなく、FIRE後に自分で納付が必要になる固定費として、
    # 安全・推奨・上限生活費それぞれから直接差し引く。ガードレール判定
    # （green/yellow/red）自体はこの控除によって変化しない。
    if monthly_social_insurance > 0.005:
        safe_monthly = round(max(safe_monthly - monthly_social_insurance, 0.0), 2)
        recommended_monthly = round(
            max(recommended_monthly - monthly_social_insurance, 0.0), 2
        )
        max_monthly = round(max(max_monthly - monthly_social_insurance, 0.0), 2)
        reasons.append("social_insurance_deducted")

    return MonthlyBudgetResult(
        safe_monthly=safe_monthly,
        recommended_monthly=recommended_monthly,
        max_monthly=max_monthly,
        status=status,
        reasons=reasons,
        binding_safe_factor_reason=binding_reason,
    )
