from pathlib import Path

import numpy as np
import pandas as pd

from src.data.market import get_stock_data
from src.models.features import (
    FEATURE_COLUMNS,
    build_features,
)


OUTPUT = Path("training_dataset.npz")

HORIZON = 5
LOOKBACK = 64


def direction_class(return_value):

    if return_value <= -0.05:
        return 0

    if return_value <= -0.015:
        return 1

    if return_value < 0.015:
        return 2

    if return_value < 0.05:
        return 3

    return 4


def process_stock(ticker):

    df = get_stock_data(
        ticker,
        period="10y",
        interval="1d",
    )

    if df.empty:
        return [], [], []

    features = build_features(df)

    future_return = (
        df["Close"].shift(-HORIZON)
        / df["Close"]
        - 1
    )

    features["future_return"] = future_return

    X = []
    y_direction = []
    y_returns = []

    for i in range(
        LOOKBACK,
        len(features) - HORIZON,
    ):

        window = (
            features[
                FEATURE_COLUMNS
            ]
            .iloc[
                i - LOOKBACK:i
            ]
        )

        if window.isna().any().any():
            continue

        target_return = (
            future_return.iloc[i]
        )

        if pd.isna(target_return):
            continue

        window = window.replace(
            [np.inf, -np.inf],
            np.nan,
        ).ffill().bfill()

        if window.isna().any().any():
            continue

        X.append(
            window.to_numpy(
                dtype=np.float32
            )
        )

        y_direction.append(
            direction_class(
                target_return
            )
        )

        y_returns.append(
            [
                float(
                    df["Close"].shift(-1).iloc[i]
                    / df["Close"].iloc[i]
                    - 1
                ),
                float(target_return),
                float(
                    df["Close"].shift(-20).iloc[i]
                    / df["Close"].iloc[i]
                    - 1
                )
                if i + 20 < len(df)
                else float(target_return),
            ]
        )

    return X, y_direction, y_returns


def build_dataset(tickers):

    all_X = []
    all_y_direction = []
    all_y_returns = []

    for ticker in tickers:

        try:
            X, y, r = process_stock(ticker)

            all_X.extend(X)
            all_y_direction.extend(y)
            all_y_returns.extend(r)

            print(
                ticker,
                len(X),
            )

        except Exception as exc:
            print(
                "FAILED",
                ticker,
                exc,
            )

    X = np.asarray(
        all_X,
        dtype=np.float32,
    )

    y_direction = np.asarray(
        all_y_direction,
        dtype=np.int64,
    )

    y_returns = np.asarray(
        all_y_returns,
        dtype=np.float32,
    )

    np.savez_compressed(
        OUTPUT,
        X=X,
        y_direction=y_direction,
        y_returns=y_returns,
    )

    print("Saved:", OUTPUT)
    print("Samples:", len(X))


if __name__ == "__main__":

    # Replace this with a proper maintained
    # NYSE/NASDAQ/ETF universe in production.
    tickers = [
        "AAPL",
        "MSFT",
        "NVDA",
        "AMZN",
        "GOOGL",
        "META",
        "TSLA",
        "AVGO",
        "JPM",
        "V",
        "MA",
        "UNH",
        "XOM",
        "COST",
        "HD",
        "PG",
        "KO",
        "PEP",
        "NFLX",
        "AMD",
    ]

    build_dataset(tickers)