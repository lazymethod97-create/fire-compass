from dataclasses import dataclass

import pandas as pd
import yfinance as yf

from services.crash_strategy import STRATEGIES as _CRASH_STRATEGIES

# Sprint 25で追加。S&P500の過去最高値からの下落率をもとに、
# crash_strategy.STRATEGIESのキーと同じ市場環境ラベルを自動判定する。
#
# このモジュールは「価格データの取得」と「下落率→ラベルへの変換」のみを
# 行い、crash_strategy.pyの戦略計算ロジックには一切手を加えない。
# 自動判定はあくまで初期値の提案であり、呼び出し側（app.py）は必ず
# 手動での上書きを可能にする（非公式ライブラリへの依存によるアプリ全体の
# 不安定化を避けるための設計方針）。

DEFAULT_TICKER = "^GSPC"  # S&P500。Sprint22のsequence_risk_engineと一貫。

_NORMAL_CONDITION = "通常"

# 下落率のしきい値（下から順に判定）。一般的な金融用語の定義に基づく：
# 10%未満=通常、10〜20%未満=弱気相場、20〜35%未満=暴落、35%以上=深刻な暴落。
#
# Sprint 27で修正。しきい値の割合(0.10/0.20/0.35)自体はcrash_strategy.py
# 側に定義がないため、ここに残すしかないが、対応するラベル文字列は
# crash_strategy.STRATEGIESのキーをそのまま使う（このモジュールで独自に
# 同じ文字列をハードコードしない）。crash_strategy.py（ロック済み）の
# 市場環境の種類が将来増減した場合に、ラベルの表記だけが2箇所で
# 食い違ってしまうのを防ぐための、唯一の情報源（single source of truth）
# 化。万一crash_strategy.STRATEGIESのキーが変わってここと不整合になった
# 場合は、モジュール読み込み時にAssertionErrorで検知する。
_THRESHOLDS = (
    (0.35, "深刻な暴落"),
    (0.20, "暴落"),
    (0.10, "弱気相場"),
)

for _threshold, _condition_label in _THRESHOLDS:
    assert _condition_label in _CRASH_STRATEGIES, (
        f"market_data_engine._THRESHOLDSのラベル'{_condition_label}'が"
        "crash_strategy.STRATEGIESに存在しません。"
        "crash_strategy.pyの市場環境の種類が変更された場合は、"
        "market_data_engine._THRESHOLDSも合わせて見直してください。"
    )
assert _NORMAL_CONDITION in _CRASH_STRATEGIES, (
    f"market_data_engine._NORMAL_CONDITION'{_NORMAL_CONDITION}'が"
    "crash_strategy.STRATEGIESに存在しません。"
)


class MarketDataError(Exception):
    """市場データの取得・算出に失敗した場合の例外。

    呼び出し側はこの例外を捕捉し、手動選択にフォールバックすることを
    想定している。
    """


@dataclass
class MarketConditionResult:
    condition: str
    drawdown_pct: float
    current_price: float
    all_time_high: float
    ticker: str


def _condition_for_drawdown(drawdown_pct: float) -> str:
    for threshold, label in _THRESHOLDS:
        if drawdown_pct >= threshold:
            return label
    return _NORMAL_CONDITION


def determine_condition_from_prices(
    prices: pd.Series,
    ticker: str = DEFAULT_TICKER,
) -> MarketConditionResult:
    """時系列順の価格（日次終値等）から、無期限（取得できた全期間）の
    過去最高値を基準にした下落率と、対応する市場環境ラベルを算出する。

    ネットワーク通信を行わない純粋な計算関数のため、単体テストが容易。
    """
    if prices is None or len(prices) == 0:
        raise MarketDataError("価格データが空です。")

    # yfinanceは当日分の未確定データ等でNaN行を返すことがあるため、
    # 欠損値を除外してから最高値・直近値を算出する。
    valid_prices = prices.dropna()

    if valid_prices.empty:
        raise MarketDataError("有効な価格データがありません（すべて欠損値）。")

    all_time_high = float(valid_prices.max())
    current_price = float(valid_prices.iloc[-1])

    if all_time_high <= 0:
        raise MarketDataError("過去最高値が0以下のため、下落率を計算できません。")

    drawdown_pct = max((all_time_high - current_price) / all_time_high, 0.0)
    condition = _condition_for_drawdown(drawdown_pct)

    return MarketConditionResult(
        condition=condition,
        drawdown_pct=round(drawdown_pct, 4),
        current_price=round(current_price, 2),
        all_time_high=round(all_time_high, 2),
        ticker=ticker,
    )


def fetch_market_condition(
    ticker: str = DEFAULT_TICKER,
) -> MarketConditionResult:
    """yfinance経由で対象指数の日次終値（取得できる全期間）を取得し、
    現在の市場環境ラベルを自動判定する。

    yfinanceは非公式ライブラリのため、Yahoo Finance側の仕様変更や
    ネットワーク障害で失敗する可能性がある。失敗時はMarketDataErrorを
    送出するので、呼び出し側は必ずこれを捕捉して手動選択にフォールバック
    すること。
    """
    try:
        history = yf.Ticker(ticker).history(period="max", interval="1d")
    except Exception as exc:  # yfinance側の例外は多岐にわたるため包括的に捕捉
        raise MarketDataError(
            f"市場データの取得に失敗しました（{ticker}）: {exc}"
        ) from exc

    if history is None or history.empty or "Close" not in history:
        raise MarketDataError(
            f"市場データを取得できませんでした（{ticker}）。データが空です。"
        )

    return determine_condition_from_prices(history["Close"], ticker=ticker)
