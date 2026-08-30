from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from services.market_data_engine import (
    MarketDataError,
    determine_condition_from_prices,
    fetch_market_condition,
)


def test_no_drawdown_is_normal_condition():
    result = determine_condition_from_prices(pd.Series([100.0, 105.0, 110.0]))

    assert result.condition == "通常"
    assert result.drawdown_pct == 0.0


def test_small_drawdown_is_normal_condition():
    # 過去最高値110から108へ（約1.8%下落）
    result = determine_condition_from_prices(pd.Series([100.0, 110.0, 108.0]))

    assert result.condition == "通常"


def test_ten_percent_drawdown_is_bear_market():
    result = determine_condition_from_prices(pd.Series([100.0, 100.0, 90.0]))

    assert result.condition == "弱気相場"
    assert result.drawdown_pct == 0.10


def test_just_below_ten_percent_is_still_normal():
    result = determine_condition_from_prices(pd.Series([100.0, 100.0, 90.5]))

    assert result.condition == "通常"


def test_twenty_percent_drawdown_is_crash():
    result = determine_condition_from_prices(pd.Series([100.0, 100.0, 80.0]))

    assert result.condition == "暴落"
    assert result.drawdown_pct == 0.20


def test_thirty_five_percent_drawdown_is_severe_crash():
    result = determine_condition_from_prices(pd.Series([100.0, 100.0, 65.0]))

    assert result.condition == "深刻な暴落"
    assert result.drawdown_pct == 0.35


def test_all_time_high_uses_full_series_not_just_latest_peak():
    # 過去に150の高値があり、その後回復せず100まで下落した場合、
    # 直近の変動ではなく全期間の最高値(150)を基準にする。
    result = determine_condition_from_prices(
        pd.Series([80.0, 150.0, 120.0, 100.0])
    )

    expected_drawdown = round((150.0 - 100.0) / 150.0, 4)
    assert result.drawdown_pct == expected_drawdown
    assert result.all_time_high == 150.0


def test_current_price_is_last_value_in_series():
    result = determine_condition_from_prices(pd.Series([100.0, 120.0, 90.0]))

    assert result.current_price == 90.0


def test_custom_ticker_is_passed_through():
    result = determine_condition_from_prices(
        pd.Series([100.0, 100.0]), ticker="^N225"
    )

    assert result.ticker == "^N225"


def test_empty_series_raises_market_data_error():
    with pytest.raises(MarketDataError):
        determine_condition_from_prices(pd.Series([], dtype=float))


def test_none_prices_raises_market_data_error():
    with pytest.raises(MarketDataError):
        determine_condition_from_prices(None)


def test_zero_all_time_high_raises_market_data_error():
    with pytest.raises(MarketDataError):
        determine_condition_from_prices(pd.Series([0.0, 0.0]))


def test_trailing_nan_is_ignored_using_last_valid_price():
    # yfinanceが当日分の未確定データ等でNaNを返すケースを想定。
    result = determine_condition_from_prices(
        pd.Series([100.0, 100.0, 90.0, float("nan")])
    )

    assert result.current_price == 90.0
    assert result.drawdown_pct == 0.10
    assert result.condition == "弱気相場"


def test_all_nan_series_raises_market_data_error():
    with pytest.raises(MarketDataError):
        determine_condition_from_prices(
            pd.Series([float("nan"), float("nan")])
        )


def test_nan_in_middle_of_series_does_not_break_all_time_high():
    result = determine_condition_from_prices(
        pd.Series([100.0, float("nan"), 150.0, 120.0])
    )

    assert result.all_time_high == 150.0
    assert result.current_price == 120.0


def test_fetch_market_condition_success_uses_close_prices():
    mock_history = pd.DataFrame({"Close": [100.0, 100.0, 80.0]})

    with patch("services.market_data_engine.yf.Ticker") as mock_ticker_cls:
        mock_ticker_cls.return_value.history.return_value = mock_history

        result = fetch_market_condition(ticker="^GSPC")

    assert result.condition == "暴落"
    mock_ticker_cls.assert_called_once_with("^GSPC")


def test_fetch_market_condition_raises_on_network_exception():
    with patch("services.market_data_engine.yf.Ticker") as mock_ticker_cls:
        mock_ticker_cls.return_value.history.side_effect = RuntimeError(
            "network down"
        )

        with pytest.raises(MarketDataError):
            fetch_market_condition()


def test_fetch_market_condition_raises_on_empty_history():
    with patch("services.market_data_engine.yf.Ticker") as mock_ticker_cls:
        mock_ticker_cls.return_value.history.return_value = pd.DataFrame()

        with pytest.raises(MarketDataError):
            fetch_market_condition()


def test_fetch_market_condition_raises_when_close_column_missing():
    with patch("services.market_data_engine.yf.Ticker") as mock_ticker_cls:
        mock_ticker_cls.return_value.history.return_value = pd.DataFrame(
            {"Open": [100.0, 101.0]}
        )

        with pytest.raises(MarketDataError):
            fetch_market_condition()


def test_fetch_market_condition_raises_when_history_is_none():
    with patch("services.market_data_engine.yf.Ticker") as mock_ticker_cls:
        mock_ticker_cls.return_value.history.return_value = None

        with pytest.raises(MarketDataError):
            fetch_market_condition()
