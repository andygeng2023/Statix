import numpy as np
import pandas as pd


def calculate_rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    return 100 - (100 / (1 + rs))


def create_features(stock_df, market_df=None, horizon=5):
    df = stock_df.copy()

    close = df["Close"]
    volume = df["Volume"]

    # Returns
    df["return_1d"] = close.pct_change(1)
    df["return_5d"] = close.pct_change(5)
    df["return_20d"] = close.pct_change(20)

    # Momentum
    df["momentum_10"] = close / close.shift(10) - 1
    df["momentum_30"] = close / close.shift(30) - 1

    # Moving averages
    df["ma10"] = close.rolling(10).mean()
    df["ma20"] = close.rolling(20).mean()
    df["ma50"] = close.rolling(50).mean()

    df["ma10_ratio"] = close / df["ma10"] - 1
    df["ma20_ratio"] = close / df["ma20"] - 1
    df["ma50_ratio"] = close / df["ma50"] - 1

    # Volatility
    df["volatility_10"] = df["return_1d"].rolling(10).std()
    df["volatility_20"] = df["return_1d"].rolling(20).std()

    # RSI
    df["rsi"] = calculate_rsi(close)

    # Volume
    volume_average = volume.rolling(20).mean()

    df["volume_ratio"] = volume / volume_average
    df["volume_change"] = volume.pct_change()

    # High-low range
    df["range_pct"] = (
        (df["High"] - df["Low"]) / close
    )

    # Market context
    if market_df is not None:
        market = market_df.copy()

        market_return = market["Close"].pct_change()

        df["market_return_1d"] = market_return.reindex(
            df.index
        ).ffill()

        df["market_return_5d"] = (
            market["Close"].pct_change(5)
            .reindex(df.index)
            .ffill()
        )

        df["market_volatility"] = (
            market_return.rolling(20).std()
            .reindex(df.index)
            .ffill()
        )

    else:
        df["market_return_1d"] = 0
        df["market_return_5d"] = 0
        df["market_volatility"] = 0

    # Future return
    df["future_return"] = (
        close.shift(-horizon) / close - 1
    )

    # Direction target
    df["target"] = (
        df["future_return"] > 0
    ).astype(int)

    feature_columns = [
        "return_1d",
        "return_5d",
        "return_20d",
        "momentum_10",
        "momentum_30",
        "ma10_ratio",
        "ma20_ratio",
        "ma50_ratio",
        "volatility_10",
        "volatility_20",
        "rsi",
        "volume_ratio",
        "volume_change",
        "range_pct",
        "market_return_1d",
        "market_return_5d",
        "market_volatility",
    ]

    return df, feature_columns