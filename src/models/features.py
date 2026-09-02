import numpy as np
import pandas as pd


def calculate_rsi(series: pd.Series, period: int = 14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    return 100 - (100 / (1 + rs))


def create_features(
    stock_df: pd.DataFrame,
    market_df: pd.DataFrame | None = None,
    horizon: int = 5,
):
    if stock_df.empty:
        return pd.DataFrame(), []

    df = stock_df.copy()

    close = df["Close"]
    volume = df["Volume"]

    # Price returns
    df["return_1d"] = close.pct_change(1)
    df["return_3d"] = close.pct_change(3)
    df["return_5d"] = close.pct_change(5)
    df["return_10d"] = close.pct_change(10)
    df["return_20d"] = close.pct_change(20)

    # Momentum
    df["momentum_10"] = close / close.shift(10) - 1
    df["momentum_30"] = close / close.shift(30) - 1

    # Moving averages
    ma10 = close.rolling(10).mean()
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    ma100 = close.rolling(100).mean()
    ma200 = close.rolling(200).mean()

    df["ma10_ratio"] = close / ma10
    df["ma20_ratio"] = close / ma20
    df["ma50_ratio"] = close / ma50
    df["ma100_ratio"] = close / ma100
    df["ma200_ratio"] = close / ma200

    df["ma10_ma50"] = ma10 / ma50
    df["ma20_ma50"] = ma20 / ma50
    df["ma50_ma200"] = ma50 / ma200

    # Volatility
    df["volatility_5"] = df["return_1d"].rolling(5).std()
    df["volatility_10"] = df["return_1d"].rolling(10).std()
    df["volatility_20"] = df["return_1d"].rolling(20).std()
    df["volatility_60"] = df["return_1d"].rolling(60).std()

    # RSI
    df["rsi"] = calculate_rsi(close)

    # Daily range
    df["range_pct"] = (df["High"] - df["Low"]) / close

    # Volume
    volume_avg = volume.rolling(20).mean()

    df["volume_ratio"] = volume / volume_avg
    df["volume_change"] = volume.pct_change()

    # Market context
    if market_df is not None and not market_df.empty:
        market = market_df[["Close"]].copy()
        market["market_return_1d"] = market["Close"].pct_change()
        market["market_return_5d"] = market["Close"].pct_change(5)
        market["market_trend"] = (
            market["Close"] / market["Close"].rolling(50).mean()
        )
        market["market_volatility"] = (
            market["market_return_1d"].rolling(20).std()
        )

        df = df.join(
            market[
                [
                    "market_return_1d",
                    "market_return_5d",
                    "market_trend",
                    "market_volatility",
                ]
            ],
            how="left",
        )

        df["relative_return_5d"] = (
            df["return_5d"] - df["market_return_5d"]
        )

    else:
        df["market_return_1d"] = 0.0
        df["market_return_5d"] = 0.0
        df["market_trend"] = 1.0
        df["market_volatility"] = 0.0
        df["relative_return_5d"] = df["return_5d"]

    # Future target
    df["future_return"] = close.shift(-horizon) / close - 1
    df["target"] = (df["future_return"] > 0).astype(int)

    feature_columns = [
        "return_1d",
        "return_3d",
        "return_5d",
        "return_10d",
        "return_20d",
        "momentum_10",
        "momentum_30",
        "ma10_ratio",
        "ma20_ratio",
        "ma50_ratio",
        "ma100_ratio",
        "ma200_ratio",
        "ma10_ma50",
        "ma20_ma50",
        "ma50_ma200",
        "volatility_5",
        "volatility_10",
        "volatility_20",
        "volatility_60",
        "rsi",
        "range_pct",
        "volume_ratio",
        "volume_change",
        "market_return_1d",
        "market_return_5d",
        "market_trend",
        "market_volatility",
        "relative_return_5d",
    ]

    # Only remove rows after ALL features have been created.
    # This is what prevents the previous historical-context issue
    # from unnecessarily rejecting otherwise valid stocks.
    usable = df.dropna(
        subset=feature_columns + ["future_return", "target"]
    ).copy()

    return usable, feature_columns