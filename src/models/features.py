import numpy as np
import pandas as pd


def calculate_rsi(
    series,
    period=14,
):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    average_gain = gain.rolling(
        period
    ).mean()

    average_loss = loss.rolling(
        period
    ).mean()

    rs = (
        average_gain
        / average_loss.replace(0, np.nan)
    )

    return 100 - (
        100 / (1 + rs)
    )


def create_features(
    stock_df,
    market_df=None,
    horizon=5,
):
    df = stock_df.copy()

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # -------------------------
    # Returns
    # -------------------------

    df["return_1d"] = close.pct_change(1)
    df["return_3d"] = close.pct_change(3)
    df["return_5d"] = close.pct_change(5)
    df["return_10d"] = close.pct_change(10)
    df["return_20d"] = close.pct_change(20)

    # -------------------------
    # Momentum
    # -------------------------

    df["momentum_10"] = (
        close / close.shift(10) - 1
    )

    df["momentum_30"] = (
        close / close.shift(30) - 1
    )

    # -------------------------
    # Moving averages
    # -------------------------

    ma10 = close.rolling(10).mean()
    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    ma100 = close.rolling(100).mean()

    df["ma10_ratio"] = (
        close / ma10 - 1
    )

    df["ma20_ratio"] = (
        close / ma20 - 1
    )

    df["ma50_ratio"] = (
        close / ma50 - 1
    )

    df["ma100_ratio"] = (
        close / ma100 - 1
    )

    # -------------------------
    # Trend structure
    # -------------------------

    df["ma10_ma50"] = (
        ma10 / ma50 - 1
    )

    df["ma20_ma50"] = (
        ma20 / ma50 - 1
    )

    # -------------------------
    # Volatility
    # -------------------------

    daily_return = close.pct_change()

    df["volatility_5"] = (
        daily_return.rolling(5).std()
    )

    df["volatility_10"] = (
        daily_return.rolling(10).std()
    )

    df["volatility_20"] = (
        daily_return.rolling(20).std()
    )

    # -------------------------
    # RSI
    # -------------------------

    df["rsi"] = calculate_rsi(
        close,
        14,
    )

    # -------------------------
    # Price range
    # -------------------------

    df["range_pct"] = (
        (high - low) / close
    )

    # -------------------------
    # Volume
    # -------------------------

    volume_average = volume.rolling(
        20
    ).mean()

    df["volume_ratio"] = (
        volume / volume_average
    )

    df["volume_change"] = (
        volume.pct_change()
    )

    # -------------------------
    # Market context
    # -------------------------

    if market_df is not None:

        market = market_df.copy()

        market_close = market["Close"]

        market_return = (
            market_close.pct_change()
        )

        market_ma20 = (
            market_close.rolling(20).mean()
        )

        market_ma50 = (
            market_close.rolling(50).mean()
        )

        market_return_5 = (
            market_close.pct_change(5)
        )

        market_volatility = (
            market_return.rolling(20).std()
        )

        df["market_return_1d"] = (
            market_return
            .reindex(df.index)
            .ffill()
        )

        df["market_return_5d"] = (
            market_return_5
            .reindex(df.index)
            .ffill()
        )

        df["market_trend"] = (
            (
                market_ma20 / market_ma50
            )
            .reindex(df.index)
            .ffill()
            - 1
        )

        df["market_volatility"] = (
            market_volatility
            .reindex(df.index)
            .ffill()
        )

        # Relative stock performance
        df["relative_return_5d"] = (
            df["return_5d"]
            - df["market_return_5d"]
        )

    else:

        for column in [
            "market_return_1d",
            "market_return_5d",
            "market_trend",
            "market_volatility",
            "relative_return_5d",
        ]:
            df[column] = 0.0

    # -------------------------
    # Prediction targets
    # -------------------------

    df["future_return"] = (
        close.shift(-horizon)
        / close
        - 1
    )

    df["target"] = (
        df["future_return"] > 0
    ).astype(int)

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
        "ma10_ma50",
        "ma20_ma50",
        "volatility_5",
        "volatility_10",
        "volatility_20",
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

    return df, feature_columns