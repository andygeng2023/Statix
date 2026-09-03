from __future__ import annotations

import numpy as np
import pandas as pd


FEATURE_VERSION = (
    "statix-v7.2-features-1"
)


def calculate_rsi(
    series: pd.Series,
    period: int = 14,
) -> pd.Series:

    delta = series.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    avg_gain = gain.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False,
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        min_periods=period,
        adjust=False,
    ).mean()

    rs = (
        avg_gain
        / avg_loss.replace(
            0,
            np.nan,
        )
    )

    return 100 - (
        100 / (1 + rs)
    )


def calculate_atr(
    df: pd.DataFrame,
    period: int = 14,
) -> pd.Series:

    previous_close = (
        df["close"].shift(1)
    )

    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (
                df["high"]
                - previous_close
            ).abs(),
            (
                df["low"]
                - previous_close
            ).abs(),
        ],
        axis=1,
    ).max(axis=1)

    return true_range.rolling(
        period
    ).mean()


def _add_market_features(
    df: pd.DataFrame,
    market_df: pd.DataFrame | None,
) -> pd.DataFrame:

    if (
        market_df is None
        or market_df.empty
        or "close" not in market_df.columns
    ):

        df["market_return_1d"] = 0.0
        df["market_return_5d"] = 0.0
        df["market_return_20d"] = 0.0
        df["market_volatility"] = 0.0
        df["market_trend"] = 1.0
        df["relative_return_5d"] = (
            df["return_5d"]
        )

        return df

    market = market_df.copy()

    market_close = pd.to_numeric(
        market["close"],
        errors="coerce",
    )

    market_features = pd.DataFrame(
        index=market.index
    )

    market_features[
        "market_return_1d"
    ] = market_close.pct_change(1)

    market_features[
        "market_return_5d"
    ] = market_close.pct_change(5)

    market_features[
        "market_return_20d"
    ] = market_close.pct_change(20)

    market_features[
        "market_volatility"
    ] = (
        market_close
        .pct_change()
        .rolling(20)
        .std()
    )

    ma50 = market_close.rolling(
        50
    ).mean()

    ma200 = market_close.rolling(
        200
    ).mean()

    market_features[
        "market_trend"
    ] = ma50 / ma200

    df = df.join(
        market_features,
        how="left",
    )

    df[
        "relative_return_5d"
    ] = (
        df["return_5d"]
        - df["market_return_5d"]
    )

    return df


def create_features(
    stock_df: pd.DataFrame,
    market_df: pd.DataFrame | None = None,
    horizon: int = 5,
):
    """
    Creates model features.

    Returns:
        training_df
        latest_df
        feature_columns

    The latest row does not need a future target because
    it is used for the current prediction.
    """

    if (
        stock_df is None
        or stock_df.empty
    ):
        raise ValueError(
            "No stock data available."
        )

    df = stock_df.copy()

    required = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Missing market columns: "
            + ", ".join(missing)
        )

    for column in required:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.sort_index()

    close = df["close"]
    volume = df["volume"]

    # Returns.
    for period in [
        1,
        2,
        3,
        5,
        10,
        20,
        60,
    ]:

        df[
            f"return_{period}d"
        ] = close.pct_change(
            period
        )

    # Momentum.
    for period in [
        5,
        10,
        20,
        60,
    ]:

        df[
            f"momentum_{period}"
        ] = (
            close
            / close.shift(period)
            - 1
        )

    # Price relative to moving averages.
    for period in [
        10,
        20,
        50,
        100,
        200,
    ]:

        ma = close.rolling(
            period
        ).mean()

        df[
            f"price_ma{period}"
        ] = close / ma

    # Moving average relationships.
    df["ma10_ma20"] = (
        close.rolling(10).mean()
        / close.rolling(20).mean()
    )

    df["ma20_ma50"] = (
        close.rolling(20).mean()
        / close.rolling(50).mean()
    )

    df["ma50_ma100"] = (
        close.rolling(50).mean()
        / close.rolling(100).mean()
    )

    df["ma50_ma200"] = (
        close.rolling(50).mean()
        / close.rolling(200).mean()
    )

    # Volatility.
    returns = close.pct_change()

    for period in [
        5,
        10,
        20,
        60,
    ]:

        df[
            f"volatility_{period}"
        ] = (
            returns
            .rolling(period)
            .std()
        )

    # RSI.
    for period in [
        7,
        14,
        21,
    ]:

        df[
            f"rsi_{period}"
        ] = calculate_rsi(
            close,
            period,
        )

    # ATR.
    df["atr_14"] = calculate_atr(
        df,
        14,
    )

    df["atr_pct"] = (
        df["atr_14"]
        / close
    )

    # MACD.
    ema12 = close.ewm(
        span=12,
        adjust=False,
    ).mean()

    ema26 = close.ewm(
        span=26,
        adjust=False,
    ).mean()

    df["macd"] = (
        ema12 - ema26
    )

    df["macd_signal"] = (
        df["macd"]
        .ewm(
            span=9,
            adjust=False,
        )
        .mean()
    )

    df["macd_histogram"] = (
        df["macd"]
        - df["macd_signal"]
    )

    # Bollinger bands.
    bb_mid = close.rolling(
        20
    ).mean()

    bb_std = close.rolling(
        20
    ).std()

    bb_upper = (
        bb_mid + 2 * bb_std
    )

    bb_lower = (
        bb_mid - 2 * bb_std
    )

    df["bb_width"] = (
        (bb_upper - bb_lower)
        / bb_mid
    )

    df["bb_position"] = (
        (close - bb_lower)
        / (bb_upper - bb_lower)
    )

    # Daily range and gaps.
    df["range_pct"] = (
        (df["high"] - df["low"])
        / close
    )

    df["gap_pct"] = (
        df["open"]
        / close.shift(1)
        - 1
    )

    # Volume.
    volume_ma20 = volume.rolling(
        20
    ).mean()

    df["volume_ratio"] = (
        volume
        / volume_ma20
    )

    df["volume_change"] = (
        volume.pct_change()
    )

    df["volume_volatility"] = (
        volume
        .pct_change()
        .rolling(20)
        .std()
    )

    df["price_volume_corr"] = (
        close
        .pct_change()
        .rolling(20)
        .corr(
            volume.pct_change()
        )
    )

    # One-year drawdown and low distance.
    rolling_high = close.rolling(
        252
    ).max()

    df["drawdown_1y"] = (
        close
        / rolling_high
        - 1
    )

    rolling_low = close.rolling(
        252
    ).min()

    df["distance_1y_low"] = (
        close
        / rolling_low
        - 1
    )

    # Market context.
    df = _add_market_features(
        df,
        market_df,
    )

    # Future return.
    df["future_return"] = (
        close.shift(-horizon)
        / close
        - 1
    )

    # Five prediction classes.
    #
    # 0 Strong Bearish
    # 1 Bearish
    # 2 Neutral
    # 3 Bullish
    # 4 Strong Bullish

    future = df[
        "future_return"
    ]

    df["target"] = np.select(
        [
            future <= -0.02,
            future <= -0.005,
            future < 0.005,
            future < 0.02,
        ],
        [
            0,
            1,
            2,
            3,
        ],
        default=4,
    ).astype(float)

    excluded = {
        "open",
        "high",
        "low",
        "close",
        "volume",
        "future_return",
        "target",
    }

    feature_columns = [
        column
        for column in df.columns
        if column not in excluded
    ]

    df[feature_columns] = (
        df[feature_columns]
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
    )

    # Training rows need a known future.
    training_df = df.dropna(
        subset=(
            feature_columns
            + [
                "future_return",
                "target",
            ]
        )
    ).copy()

    # The latest row only needs features.
    latest_df = (
        df.dropna(
            subset=feature_columns
        )
        .tail(1)
        .copy()
    )

    return (
        training_df,
        latest_df,
        feature_columns,
    )