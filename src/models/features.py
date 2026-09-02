import numpy as np
import pandas as pd


FEATURE_VERSION = "statix-v6-features-2"


def calculate_rsi(series: pd.Series, period: int = 14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    return 100 - (100 / (1 + rs))


def _true_range(df):

    previous_close = df["Close"].shift(1)

    ranges = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - previous_close).abs(),
            (df["Low"] - previous_close).abs(),
        ],
        axis=1,
    )

    return ranges.max(axis=1)


def _safe_beta(stock_returns, market_returns, window=60):

    covariance = stock_returns.rolling(window).cov(
        market_returns
    )

    market_variance = market_returns.rolling(window).var()

    return covariance / market_variance.replace(0, np.nan)


def build_feature_frame(
    stock_df: pd.DataFrame,
    market_df: pd.DataFrame | None = None,
):

    df = stock_df.copy()

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    returns = close.pct_change()

    # -------------------------
    # Returns
    # -------------------------

    for period in [1, 2, 3, 5, 10, 20, 30, 60]:
        df[f"return_{period}d"] = close.pct_change(period)

    # -------------------------
    # Momentum
    # -------------------------

    for period in [5, 10, 20, 30, 60]:
        df[f"momentum_{period}d"] = (
            close / close.shift(period) - 1
        )

    df["roc_10"] = close.pct_change(10)
    df["roc_20"] = close.pct_change(20)

    # -------------------------
    # Moving averages
    # -------------------------

    for period in [10, 20, 50, 100, 200]:
        ma = close.rolling(period).mean()

        df[f"price_ma{period}"] = close / ma
        df[f"ma{period}"] = ma

    df["ma10_ma20"] = df["ma10"] / df["ma20"]
    df["ma20_ma50"] = df["ma20"] / df["ma50"]
    df["ma50_ma100"] = df["ma50"] / df["ma100"]
    df["ma50_ma200"] = df["ma50"] / df["ma200"]

    # -------------------------
    # Volatility
    # -------------------------

    for period in [5, 10, 20, 30, 60]:
        df[f"volatility_{period}d"] = (
            returns.rolling(period).std()
            * np.sqrt(252)
        )

    # -------------------------
    # ATR
    # -------------------------

    true_range = _true_range(df)

    df["atr_14"] = true_range.rolling(14).mean()
    df["atr_pct"] = df["atr_14"] / close

    # -------------------------
    # RSI
    # -------------------------

    for period in [7, 14, 21]:
        df[f"rsi_{period}"] = calculate_rsi(
            close,
            period,
        )

    # -------------------------
    # MACD
    # -------------------------

    ema12 = close.ewm(
        span=12,
        adjust=False,
    ).mean()

    ema26 = close.ewm(
        span=26,
        adjust=False,
    ).mean()

    df["macd"] = ema12 - ema26

    df["macd_signal"] = df["macd"].ewm(
        span=9,
        adjust=False,
    ).mean()

    df["macd_hist"] = (
        df["macd"] - df["macd_signal"]
    )

    # -------------------------
    # Bollinger Bands
    # -------------------------

    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()

    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std

    df["bb_width"] = (
        (bb_upper - bb_lower) / bb_mid
    )

    df["bb_position"] = (
        (close - bb_lower)
        / (bb_upper - bb_lower)
    )

    # -------------------------
    # Stochastic oscillator
    # -------------------------

    lowest_low = low.rolling(14).min()
    highest_high = high.rolling(14).max()

    denominator = (
        highest_high - lowest_low
    ).replace(0, np.nan)

    df["stoch_k"] = (
        100 * (close - lowest_low) / denominator
    )

    df["stoch_d"] = (
        df["stoch_k"].rolling(3).mean()
    )

    # -------------------------
    # Price structure
    # -------------------------

    df["range_pct"] = (
        high - low
    ) / close

    df["close_location"] = (
        close - low
    ) / (high - low).replace(0, np.nan)

    df["gap_pct"] = (
        df["Open"] / close.shift(1) - 1
    )

    # -------------------------
    # Volume
    # -------------------------

    volume_ma20 = volume.rolling(20).mean()

    df["volume_ratio"] = (
        volume / volume_ma20
    )

    df["volume_change"] = volume.pct_change()

    df["volume_volatility"] = (
        volume.pct_change()
        .rolling(20)
        .std()
    )

    df["price_volume_corr"] = (
        returns.rolling(20).corr(
            volume.pct_change()
        )
    )

    # -------------------------
    # OBV
    # -------------------------

    direction = np.sign(close.diff()).fillna(0)

    df["obv"] = (
        direction * volume
    ).cumsum()

    df["obv_change_20"] = (
        df["obv"] / df["obv"].shift(20) - 1
    )

    # -------------------------
    # Drawdown / 52-week context
    # -------------------------

    rolling_high = close.rolling(252).max()
    rolling_low = close.rolling(252).min()

    df["drawdown_252"] = (
        close / rolling_high - 1
    )

    df["distance_52w_high"] = (
        close / rolling_high - 1
    )

    df["distance_52w_low"] = (
        close / rolling_low - 1
    )

    # -------------------------
    # Market-relative features
    # -------------------------

    if market_df is not None and not market_df.empty:

        market = market_df[["Close"]].copy()

        market.columns = ["MarketClose"]

        combined = df[["Close"]].join(
            market,
            how="inner",
        )

        stock_ret = combined["Close"].pct_change()
        market_ret = combined["MarketClose"].pct_change()

        for period in [1, 5, 20, 60]:
            df[f"market_return_{period}d"] = (
                market_ret.rolling(period).sum()
            )

        df["relative_return_5d"] = (
            stock_ret.rolling(5).sum()
            - market_ret.rolling(5).sum()
        )

        df["relative_return_20d"] = (
            stock_ret.rolling(20).sum()
            - market_ret.rolling(20).sum()
        )

        df["market_volatility_20d"] = (
            market_ret.rolling(20).std()
            * np.sqrt(252)
        )

        market_ma50 = (
            combined["MarketClose"]
            .rolling(50)
            .mean()
        )

        df["market_trend"] = (
            combined["MarketClose"]
            / market_ma50
        )

        df["beta_60"] = _safe_beta(
            stock_ret,
            market_ret,
            60,
        )

    else:

        for col in [
            "market_return_1d",
            "market_return_5d",
            "market_return_20d",
            "market_return_60d",
            "relative_return_5d",
            "relative_return_20d",
            "market_volatility_20d",
            "market_trend",
            "beta_60",
        ]:
            df[col] = 0.0

    return df


def classify_return(value):

    if pd.isna(value):
        return np.nan

    if value >= 0.02:
        return 4

    if value >= 0.005:
        return 3

    if value > -0.005:
        return 2

    if value > -0.02:
        return 1

    return 0


def create_features(
    stock_df: pd.DataFrame,
    market_df: pd.DataFrame | None = None,
    horizon: int = 5,
):

    df = build_feature_frame(
        stock_df,
        market_df,
    )

    df["future_return"] = (
        df["Close"].shift(-horizon)
        / df["Close"]
        - 1
    )

    df["target"] = df["future_return"].apply(
        classify_return
    )

    ignored = {
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "ma10",
        "ma20",
        "ma50",
        "ma100",
        "ma200",
        "future_return",
        "target",
    }

    feature_columns = [
        col
        for col in df.columns
        if col not in ignored
    ]

    df[feature_columns] = (
        df[feature_columns]
        .replace([np.inf, -np.inf], np.nan)
    )

    training_df = df.dropna(
        subset=feature_columns + [
            "future_return",
            "target",
        ]
    ).copy()

    latest_df = df.dropna(
        subset=feature_columns
    ).copy()

    return (
        training_df,
        latest_df,
        feature_columns,
    )