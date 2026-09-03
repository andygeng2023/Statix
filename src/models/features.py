import numpy as np
import pandas as pd


FEATURE_VERSION = "statix-v11-features-1"


FEATURE_COLUMNS = [
    "ret_1",
    "ret_2",
    "ret_5",
    "ret_10",
    "ret_20",
    "ret_60",

    "mom_5",
    "mom_10",
    "mom_20",
    "mom_60",

    "ma_10",
    "ma_20",
    "ma_50",
    "ma_100",
    "ma_200",

    "vol_5",
    "vol_20",
    "vol_60",

    "rsi_14",

    "atr_pct",

    "macd",
    "macd_signal",

    "bb_position",

    "volume_ratio",

    "range_pct",

    "gap",
]


def _rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    return 100 - (100 / (1 + rs))


def build_features(df: pd.DataFrame) -> pd.DataFrame:

    x = df.copy()

    close = x["Close"]
    high = x["High"]
    low = x["Low"]
    open_ = x["Open"]
    volume = x["Volume"]

    for n in [1, 2, 5, 10, 20, 60]:
        x[f"ret_{n}"] = close.pct_change(n)

    for n in [5, 10, 20, 60]:
        x[f"mom_{n}"] = close / close.shift(n) - 1

    for n in [10, 20, 50, 100, 200]:
        ma = close.rolling(n).mean()
        x[f"ma_{n}"] = close / ma - 1

    returns = close.pct_change()

    for n in [5, 20, 60]:
        x[f"vol_{n}"] = returns.rolling(n).std()

    x["rsi_14"] = _rsi(close, 14) / 100.0

    previous_close = close.shift(1)

    tr = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = tr.rolling(14).mean()

    x["atr_pct"] = atr / close

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()

    x["macd"] = macd / close
    x["macd_signal"] = signal / close

    middle = close.rolling(20).mean()
    std = close.rolling(20).std()

    upper = middle + 2 * std
    lower = middle - 2 * std

    x["bb_position"] = (
        (close - lower) /
        (upper - lower).replace(0, np.nan)
    )

    volume_mean = volume.rolling(20).mean()

    x["volume_ratio"] = (
        volume /
        volume_mean.replace(0, np.nan)
    )

    x["range_pct"] = (high - low) / close

    x["gap"] = open_ / previous_close - 1

    return x


def make_sequence(
    df: pd.DataFrame,
    lookback: int = 64,
):
    features = build_features(df)

    clean = features[FEATURE_COLUMNS].replace(
        [np.inf, -np.inf],
        np.nan,
    )

    if len(clean) < lookback:
        return None

    recent = clean.tail(lookback)

    recent = recent.ffill().bfill()

    if recent.isna().any().any():
        return None

    return recent.to_numpy(dtype=np.float32)