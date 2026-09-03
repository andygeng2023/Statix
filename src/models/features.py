import numpy as np
import pandas as pd

from src.config import SETTINGS


FEATURE_VERSION = SETTINGS.feature_version


FEATURES = [
    "ret_1",
    "ret_5",
    "ret_20",
    "ret_60",

    "mom_5",
    "mom_20",
    "mom_60",

    "ma10_ratio",
    "ma20_ratio",
    "ma50_ratio",
    "ma200_ratio",

    "vol10",
    "vol20",
    "vol60",

    "rsi14",

    "atr14",

    "macd",
    "macd_signal",

    "bb_position",

    "range_pct",

    "volume_ratio",

    "volume_z",

    "drawdown_60",

    "market_ret_5",
    "market_ret_20",
]


def rsi(
    series: pd.Series,
    period: int = 14,
) -> pd.Series:

    delta = series.diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False,
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False,
    ).mean()

    rs = (
        avg_gain /
        avg_loss.replace(0, np.nan)
    )

    return 100 - (
        100 / (1 + rs)
    )


def create_features(
    stock_df: pd.DataFrame,
    market_df: pd.DataFrame | None = None,
    horizon: int = 5,
):

    if stock_df.empty:
        raise ValueError(
            "No stock data available."
        )

    x = stock_df.copy()

    close = x["Close"].astype(float)

    high = x["High"].astype(float)

    low = x["Low"].astype(float)

    volume = x["Volume"].astype(float)

    x["ret_1"] = close.pct_change(1)

    x["ret_5"] = close.pct_change(5)

    x["ret_20"] = close.pct_change(20)

    x["ret_60"] = close.pct_change(60)

    x["mom_5"] = (
        close / close.shift(5) - 1
    )

    x["mom_20"] = (
        close / close.shift(20) - 1
    )

    x["mom_60"] = (
        close / close.shift(60) - 1
    )

    for period in [10, 20, 50, 200]:

        x[f"ma{period}_ratio"] = (
            close /
            close.rolling(period).mean()
            - 1
        )

    daily_return = close.pct_change()

    x["vol10"] = (
        daily_return
        .rolling(10)
        .std()
    )

    x["vol20"] = (
        daily_return
        .rolling(20)
        .std()
    )

    x["vol60"] = (
        daily_return
        .rolling(60)
        .std()
    )

    x["rsi14"] = rsi(close, 14)

    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    x["atr14"] = (
        true_range
        .rolling(14)
        .mean()
        / close
    )

    ema12 = close.ewm(
        span=12,
        adjust=False,
    ).mean()

    ema26 = close.ewm(
        span=26,
        adjust=False,
    ).mean()

    x["macd"] = ema12 - ema26

    x["macd_signal"] = (
        x["macd"]
        .ewm(
            span=9,
            adjust=False,
        )
        .mean()
    )

    middle = (
        close
        .rolling(20)
        .mean()
    )

    std = (
        close
        .rolling(20)
        .std()
    )

    upper = middle + 2 * std

    lower = middle - 2 * std

    band_width = (
        upper - lower
    ).replace(0, np.nan)

    x["bb_position"] = (
        (close - lower)
        / band_width
    )

    x["range_pct"] = (
        (high - low) / close
    )

    volume_mean = (
        volume
        .rolling(20)
        .mean()
    )

    volume_std = (
        volume
        .rolling(20)
        .std()
    )

    x["volume_ratio"] = (
        volume / volume_mean
    )

    x["volume_z"] = (
        (volume - volume_mean)
        / volume_std.replace(0, np.nan)
    )

    rolling_max = (
        close
        .rolling(60)
        .max()
    )

    x["drawdown_60"] = (
        close / rolling_max - 1
    )

    if (
        market_df is not None
        and not market_df.empty
    ):

        market_close = (
            market_df["Close"]
            .astype(float)
            .reindex(x.index)
            .ffill()
        )

        x["market_ret_5"] = (
            market_close.pct_change(5)
        )

        x["market_ret_20"] = (
            market_close.pct_change(20)
        )

    else:

        x["market_ret_5"] = 0.0

        x["market_ret_20"] = 0.0

    x["future_return"] = (
        close.shift(-horizon)
        / close
        - 1
    )

    x["target"] = pd.cut(
        x["future_return"],
        bins=[
            -np.inf,
            -0.06,
            -0.015,
            0.015,
            0.06,
            np.inf,
        ],
        labels=[0, 1, 2, 3, 4],
    ).astype(float)

    training = x.dropna(
        subset=FEATURES
        + [
            "target",
            "future_return",
        ]
    ).copy()

    latest = (
        x.dropna(
            subset=FEATURES
        )
        .tail(1)
        .copy()
    )

    if latest.empty:
        raise ValueError(
            "Unable to construct the latest feature row."
        )

    return (
        training,
        latest,
        FEATURES,
    )