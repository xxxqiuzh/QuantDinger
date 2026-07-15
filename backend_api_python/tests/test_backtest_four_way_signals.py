"""Backtest accepts four-way df columns with chart output['signals'] (no buy/sell)."""

from __future__ import annotations

import pandas as pd
import pytest

from app.services.backtest import BacktestService
from app.services.builtin_indicators import _builtin_specs


def _sample_df(n: int = 30) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="5min")
    close = pd.Series(range(100, 100 + n), dtype=float, index=idx)
    return pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )


FOUR_WAY_WITH_CHART_SIGNALS = """
my_indicator_name = "T"
my_indicator_description = "D"
# signal_form: four_way
# exit_owner: indicator
df = df.copy()
n = len(df)
df['open_long'] = False
df['close_long'] = False
df['open_short'] = False
df['close_short'] = False
df.at[5, 'open_long'] = True
df.at[10, 'close_long'] = True
output = {
    'name': 'T',
    'plots': [],
    'signals': [
        {'type': 'buy', 'text': 'L', 'color': '#0f0', 'data': [None] * n},
    ],
}
"""


def test_execute_indicator_four_way_with_output_signals_no_buy_sell():
    svc = BacktestService()
    df = _sample_df()
    out = svc._execute_indicator(FOUR_WAY_WITH_CHART_SIGNALS, df, backtest_params={})
    assert isinstance(out, dict)
    assert "open_long" in out
    assert bool(out["open_long"].iloc[5])
    assert bool(out["close_long"].iloc[10])


def test_execute_indicator_can_return_chart_output_plots():
    svc = BacktestService()
    df = _sample_df()
    code = """
df = df.copy()
df['open_long'] = False
df['close_long'] = False
df['open_short'] = False
df['close_short'] = False
output = {
    'name': 'Plot Test',
    'plots': [
        {'name': 'Close', 'data': df['close'].tolist(), 'color': '#fff', 'overlay': True},
    ],
    'signals': [],
}
"""

    signals, output = svc._execute_indicator(code, df, backtest_params={}, return_output=True)

    assert "open_long" in signals
    assert output["name"] == "Plot Test"
    assert output["plots"][0]["name"] == "Close"
    assert output["plots"][0]["data"] == df["close"].tolist()


def test_run_result_includes_sliced_chart_output_plots(monkeypatch):
    svc = BacktestService()
    df = _sample_df(20)
    start = df.index[5]
    end = df.index[14]
    code = """
df = df.copy()
df['open_long'] = False
df['close_long'] = False
df['open_short'] = False
df['close_short'] = False
output = {
    'name': 'Plot Test',
    'plots': [
        {'name': 'Close', 'data': df['close'].tolist(), 'color': '#fff', 'overlay': True},
    ],
    'signals': [],
}
"""

    monkeypatch.setattr(svc, "_fetch_kline_data", lambda *args, **kwargs: df)
    monkeypatch.setattr(
        svc,
        "_simulate_trading",
        lambda df_window, *args, **kwargs: ([{"time": str(df_window.index[0]), "value": 10000.0}], [], 0.0),
    )
    monkeypatch.setattr(
        svc,
        "_calculate_metrics",
        lambda *args, **kwargs: {"totalReturn": 0.0, "totalTrades": 0, "maxDrawdown": 0.0},
    )
    monkeypatch.setattr(svc, "_build_quality_checks", lambda **kwargs: [])

    result = svc.run(
        indicator_code=code,
        market="crypto",
        symbol="BTC/USDT",
        timeframe="5m",
        start_date=start,
        end_date=end,
    )

    assert result["plots"][0]["name"] == "Close"
    assert result["plots"][0]["data"] == df.loc[start:end, "close"].tolist()


def test_run_multi_timeframe_result_includes_sliced_chart_output_plots(monkeypatch):
    svc = BacktestService()
    df = _sample_df(20)
    start = df.index[5]
    end = df.index[14]
    code = """
df = df.copy()
df['open_long'] = False
df['close_long'] = False
df['open_short'] = False
df['close_short'] = False
output = {
    'name': 'Plot Test',
    'plots': [
        {'name': 'Close', 'data': df['close'].tolist(), 'color': '#fff', 'overlay': True},
    ],
    'signals': [],
}
"""

    monkeypatch.setattr(
        svc,
        "get_execution_timeframe",
        lambda *args, **kwargs: ("1m", {"enabled": True, "timeframe": "1m"}),
    )
    monkeypatch.setattr(svc, "_fetch_kline_data", lambda *args, **kwargs: df)
    monkeypatch.setattr(
        svc,
        "_simulate_trading_mtf",
        lambda **kwargs: ([{"time": str(kwargs["df_signal"].index[0]), "value": 10000.0}], [], 0.0),
    )
    monkeypatch.setattr(
        svc,
        "_calculate_metrics",
        lambda *args, **kwargs: {"totalReturn": 0.0, "totalTrades": 0, "maxDrawdown": 0.0},
    )

    result = svc.run_multi_timeframe(
        indicator_code=code,
        market="crypto",
        symbol="BTC/USDT",
        timeframe="5m",
        start_date=start,
        end_date=end,
        strategy_config={"execution": {"signalTiming": "next_bar_open"}},
    )

    assert result["plots"][0]["name"] == "Close"
    assert result["plots"][0]["data"] == df.loc[start:end, "close"].tolist()


def test_builtin_indicator_sample_executes_with_four_way_contract():
    svc = BacktestService()
    df = _sample_df(120)
    code = _builtin_specs()[0]["code"]
    out = svc._execute_indicator(code, df, backtest_params={})
    assert isinstance(out, dict)
    for col in ("open_long", "close_long", "open_short", "close_short"):
        assert col in out
        assert len(out[col]) == len(df)


def test_execute_indicator_missing_signal_columns_raises_clear_error():
    svc = BacktestService()
    df = _sample_df()
    code = """
df = df.copy()
df['some_plot_only_value'] = close.rolling(3).mean()
"""
    with pytest.raises(ValueError, match="Indicator must define either 4-way columns"):
        svc._execute_indicator(code, df, backtest_params={})
