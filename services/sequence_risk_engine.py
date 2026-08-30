import random
from dataclasses import dataclass, field
from typing import List, Optional

# 過去の株式市場（S&P500、配当込みトータルリターン）の年次リターン（%）。
# 出典：Aswath Damodaran (NYU Stern), "Historical Returns on Stocks, Bonds
# and Bills: 1928-2025"
# https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html
# （1970〜2025年、56年分を採用。データ更新日: 2026年1月5日）
#
# このモジュールは「資産が何年持つか」という確率を計算するためのもの
# ではなく、あくまで安全生活費（safe_monthly）に掛ける調整係数を
# 算出するための内部計算にのみ使用する。シミュレーション結果の確率や
# パスそのものはユーザーには表示しない（呼び出し側で係数のみを使う）。
HISTORICAL_ANNUAL_RETURNS_PCT: tuple = (
    3.56, 14.22, 18.76, -14.31, -25.90, 37.00, 23.83, -6.98, 6.51, 18.52,
    31.74, -4.70, 20.42, 22.34, 6.15, 31.24, 18.49, 5.81, 16.54, 31.48,
    -3.06, 30.23, 7.49, 9.97, 1.33, 37.20, 22.68, 33.10, 28.34, 20.89,
    -9.03, -11.85, -21.97, 28.36, 10.74, 4.83, 15.61, 5.48, -36.55, 25.94,
    14.82, 2.10, 15.89, 32.15, 13.52, 1.38, 11.77, 21.61, -4.23, 31.21,
    18.02, 28.47, -18.04, 26.06, 24.88, 17.78,
)

_EARLY_RETIREMENT_START_AGE = 60

_BLOCK_YEARS = 4
_WINDOW_YEARS = 10
_N_SIMULATIONS = 2000
_DEFAULT_RANDOM_SEED = 42

# bad_path_ratio（シミュレーション試行のうちウィンドウ内に資産が
# 枯渇した割合）に応じた安全生活費の追加調整係数。
# Sprint 21の年金ステージ係数（0.90〜0.95）と同じレンジに収めている。
_RISK_FACTOR_THRESHOLDS = (
    (0.30, 0.85),
    (0.15, 0.90),
    (0.05, 0.95),
)
_RISK_FACTOR_NEUTRAL = 1.00


@dataclass
class SequenceRiskResult:
    life_stage_applicable: bool
    risk_factor: float
    bad_path_ratio: float
    reasons: List[str] = field(default_factory=list)


def _is_early_retirement_stage(current_age: int, pension_start_age: int) -> bool:
    return _EARLY_RETIREMENT_START_AGE <= current_age < pension_start_age


def _build_recentered_returns(expected_return_pct: float) -> List[float]:
    """過去リターン系列の「形」（暴落の急峻さ・連続性）は保持したまま、
    平均だけをユーザー入力の想定利回りに合わせてシフトする。
    """
    historical_mean = sum(HISTORICAL_ANNUAL_RETURNS_PCT) / len(
        HISTORICAL_ANNUAL_RETURNS_PCT
    )
    shift = expected_return_pct - historical_mean
    return [r + shift for r in HISTORICAL_ANNUAL_RETURNS_PCT]


def _sample_block_bootstrap_path(
    returns: List[float],
    window_years: int,
    block_years: int,
    rng: random.Random,
) -> List[float]:
    """ブロックブートストラップで window_years 分のリターン系列を1本生成する。

    単年ごとの独立抽出ではなく、block_years年分をひとまとまりで抽出する
    ことで、暴落が複数年にまたがって連続するという系列リスクの本質を
    再現する。
    """
    path: List[float] = []
    max_start_index = len(returns) - block_years

    while len(path) < window_years:
        start_index = rng.randint(0, max_start_index)
        block = returns[start_index : start_index + block_years]
        path.extend(block)

    return path[:window_years]


def _simulate_window_depletes(
    start_assets: float,
    annual_net_spending: float,
    inflation_rate: float,
    return_path_pct: List[float],
) -> bool:
    """window_years分のリターン系列に沿って取り崩しを行い、
    途中で資産が枯渇するかどうかを判定する。

    fire_engine._simulateと同じ考え方（複利成長からその年の純支出を
    差し引く）を10年分の短いウィンドウに適用したもの。
    """
    assets = start_assets
    spending = annual_net_spending

    for return_pct in return_path_pct:
        assets = assets * (1.0 + return_pct / 100.0) - spending
        spending *= 1.0 + inflation_rate

        if assets <= 0:
            return True

    return False


def _factor_for_bad_path_ratio(bad_path_ratio: float) -> float:
    for threshold, factor in _RISK_FACTOR_THRESHOLDS:
        if bad_path_ratio >= threshold:
            return factor
    return _RISK_FACTOR_NEUTRAL


def calculate_sequence_risk_factor(
    current_age: int,
    pension_start_age: int,
    total_assets: float,
    annual_spending: float,
    annual_side_income: float,
    expected_return_pct: float,
    inflation_pct: float,
    window_years: int = _WINDOW_YEARS,
    n_simulations: int = _N_SIMULATIONS,
    random_seed: Optional[int] = _DEFAULT_RANDOM_SEED,
) -> SequenceRiskResult:
    """早期リタイア期（60歳〜年金受給開始前）に限定して、シーケンス・
    オブ・リターンズ・リスクをモンテカルロ（ブロックブートストラップ）で
    評価し、安全生活費に掛ける追加の調整係数を算出する。

    このエンジンはfire_engine / action_engine / monthly_budget_engineの
    既存の計算ロジックを変更しない。あくまで独立した係数を算出するだけの
    モジュールであり、返す係数をmonthly_budget_engine側で他の係数と
    比較（最小値を採用）した上で適用するかどうかを決める。

    早期リタイア期でない場合は、シミュレーションを行わずに
    risk_factor=1.00・life_stage_applicable=Falseを返す（既存呼び出しへの
    影響なし）。
    """
    if current_age < 0:
        raise ValueError("現在年齢は0以上にしてください。")
    if pension_start_age < 0:
        raise ValueError("年金受給開始年齢は0以上にしてください。")
    if total_assets < 0:
        raise ValueError("総金融資産は0以上にしてください。")
    if annual_spending < 0:
        raise ValueError("年間生活費は0以上にしてください。")
    if annual_side_income < 0:
        raise ValueError("年間副収入は0以上にしてください。")
    if window_years <= 0:
        raise ValueError("ウィンドウ年数は1以上にしてください。")
    if n_simulations <= 0:
        raise ValueError("試行回数は1以上にしてください。")
    if window_years > _BLOCK_YEARS * len(HISTORICAL_ANNUAL_RETURNS_PCT):
        raise ValueError("ウィンドウ年数が過去データに対して長すぎます。")

    if not _is_early_retirement_stage(current_age, pension_start_age):
        return SequenceRiskResult(
            life_stage_applicable=False,
            risk_factor=_RISK_FACTOR_NEUTRAL,
            bad_path_ratio=0.0,
            reasons=["not_early_retirement_stage"],
        )

    annual_net_spending = max(annual_spending - annual_side_income, 0.0)

    if annual_net_spending <= 0:
        # 支出が副収入で完全に相殺されている場合、取り崩し自体が
        # 発生しないため系列リスクの評価対象外とする。
        return SequenceRiskResult(
            life_stage_applicable=True,
            risk_factor=_RISK_FACTOR_NEUTRAL,
            bad_path_ratio=0.0,
            reasons=["no_net_withdrawal_needed"],
        )

    recentered_returns = _build_recentered_returns(expected_return_pct)
    rng = random.Random(random_seed)
    inflation_rate = inflation_pct / 100.0

    bad_paths = 0

    for _ in range(n_simulations):
        return_path = _sample_block_bootstrap_path(
            recentered_returns,
            window_years=window_years,
            block_years=_BLOCK_YEARS,
            rng=rng,
        )
        if _simulate_window_depletes(
            start_assets=total_assets,
            annual_net_spending=annual_net_spending,
            inflation_rate=inflation_rate,
            return_path_pct=return_path,
        ):
            bad_paths += 1

    bad_path_ratio = bad_paths / n_simulations
    risk_factor = _factor_for_bad_path_ratio(bad_path_ratio)

    reasons = ["early_retirement_stage_evaluated"]
    if risk_factor < _RISK_FACTOR_NEUTRAL:
        reasons.append("sequence_risk_elevated")

    return SequenceRiskResult(
        life_stage_applicable=True,
        risk_factor=risk_factor,
        bad_path_ratio=round(bad_path_ratio, 4),
        reasons=reasons,
    )
