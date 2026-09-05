from __future__ import annotations

import numpy as np
import pandas as pd

FEATURE_VERSION = "statix-point-in-time-features-v4"


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return 100 - 100 / (1 + gain / loss.replace(0, np.nan))


def _slope(series: pd.Series, period: int) -> pd.Series:
    return series.pct_change(period) / period


def _context_series(context, name: str, index: pd.Index) -> pd.Series:
    if context is None:
        return pd.Series(0.0, index=index)
    if isinstance(context, dict):
        context = context.get(name)
    if context is None or getattr(context, "empty", True):
        return pd.Series(0.0, index=index)
    return context["close"].astype(float).reindex(index).ffill()


def create_features(stock, market=None, sector=None, horizon=5, target=True):
    """Create point-in-time features and excess-return targets."""
    data = stock.copy().sort_index()
    close = data["close"].astype(float)
    volume = data["volume"].astype(float)
    returns = close.pct_change()
    true_range = pd.concat(
        [data["high"] - data["low"],
         (data["high"] - close.shift()).abs(),
         (data["low"] - close.shift()).abs()], axis=1,
    ).max(axis=1)

    for period in [1, 5, 20, 60]:
        data[f"ret_{period}"] = close.pct_change(period)
    for period in [10, 20, 50, 100, 200]:
        data[f"ma_distance_{period}"] = close / close.rolling(period).mean() - 1
        data[f"ema_distance_{period}"] = close / close.ewm(span=period, adjust=False).mean() - 1
        data[f"ma_slope_{period}"] = _slope(close.rolling(period).mean(), min(period, 20))
    for period in [5, 10, 20, 60]:
        volatility = returns.rolling(period).std()
        data[f"vol_{period}"] = volatility
        data[f"vol_percentile_{period}"] = volatility.rolling(252, min_periods=period).rank(pct=True)
    for period in [7, 14, 21]:
        data[f"rsi_{period}"] = _rsi(close, period) / 100

    data["atr_pct"] = true_range.rolling(14).mean() / close
    data["range_pct"] = (data["high"] - data["low"]) / close
    data["gap_pct"] = data["open"] / close.shift() - 1
    fast = close.ewm(span=12, adjust=False).mean()
    slow = close.ewm(span=26, adjust=False).mean()
    macd = fast - slow
    data["macd_pct"] = macd / close
    data["macd_signal_pct"] = macd.ewm(span=9, adjust=False).mean() / close

    middle = close.rolling(20).mean()
    deviation = close.rolling(20).std()
    data["bb_width"] = 4 * deviation / middle
    data["bb_pos"] = (close - (middle - 2 * deviation)) / (4 * deviation)
    data["trend_strength"] = (close.diff(14).abs() / true_range.rolling(14).mean()).clip(-10, 10)

    average_volume = volume.rolling(20).mean()
    data["volume_relative"] = volume / average_volume
    data["volume_change"] = volume.pct_change()
    data["volume_z"] = (volume - average_volume) / volume.rolling(20).std().replace(0, np.nan)
    data["obv"] = (np.sign(returns).fillna(0) * volume).cumsum()
    data["obv_slope"] = data["obv"].pct_change(20)

    market_close = _context_series(market, "SPY", data.index)
    for name in ["SPY", "QQQ", "DIA", "IWM"]:
        context_close = _context_series(market, name, data.index)
        data[f"{name.lower()}_ret_5"] = context_close.pct_change(5)
        data[f"{name.lower()}_ret_20"] = context_close.pct_change(20)
    sector_close = _context_series(sector, "sector", data.index)
    data["market_ret_5"] = market_close.pct_change(5)
    data["market_ret_20"] = market_close.pct_change(20)
    data["relative_ret_5"] = data["ret_5"] - data["market_ret_5"]
    data["relative_ret_20"] = data["ret_20"] - data["market_ret_20"]
    data["sector_ret_5"] = sector_close.pct_change(5)
    data["relative_sector_ret_5"] = data["ret_5"] - data["sector_ret_5"]
    covariance = returns.rolling(60).cov(market_close.pct_change())
    data["beta_60"] = covariance / market_close.pct_change().rolling(60).var().replace(0, np.nan)

    feature_columns = [
        column for column in data.columns
        if column not in {"open", "high", "low", "close", "volume", "future_return", "excess_return", "target"}
    ]
    if target:
        for target_horizon in [1, 5, 20]:
            stock_future = close.shift(-target_horizon) / close - 1
            market_future = market_close.shift(-target_horizon) / market_close - 1
            data[f"future_return_{target_horizon}"] = stock_future
            data[f"excess_return_{target_horizon}"] = stock_future - market_future
            data[f"target_{target_horizon}"] = pd.cut(
                data[f"excess_return_{target_horizon}"],
                [-np.inf, -0.005, 0.005, np.inf], labels=False,
            ).astype(float)
        data["future_return"] = data[f"future_return_{horizon}"]
        data["excess_return"] = data[f"excess_return_{horizon}"]
        data["target"] = pd.cut(
            data["excess_return"], [-np.inf, -0.005, 0.005, np.inf], labels=False
        ).astype(float)

    required = feature_columns + ([
        "future_return", "excess_return", "target",
        "future_return_1", "future_return_5", "future_return_20",
        "excess_return_1", "excess_return_5", "excess_return_20",
        "target_1", "target_5", "target_20",
    ] if target else [])
    clean = data.dropna(subset=required).copy()
    clean[feature_columns] = clean[feature_columns].replace([np.inf, -np.inf], np.nan)
    clean = clean.dropna(subset=feature_columns)
    return clean, feature_columns
