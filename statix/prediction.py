import numpy as np
import pandas as pd

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score


FEATURES = [
    "return_1d",
    "return_5d",
    "return_20d",
    "volatility_10d",
    "volatility_20d",
    "ma20_ratio",
    "ma50_ratio",
    "rsi",
    "volume_change",
]


def calculate_rsi(close, period=14):
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

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

    rs = avg_gain / avg_loss.replace(0, np.nan)

    return 100 - (100 / (1 + rs))


def create_features(data, horizon=5):
    df = data.copy()

    close = df["Close"]
    volume = df["Volume"]

    df["return_1d"] = close.pct_change(1)
    df["return_5d"] = close.pct_change(5)
    df["return_20d"] = close.pct_change(20)

    df["volatility_10d"] = (
        df["return_1d"].rolling(10).std()
    )

    df["volatility_20d"] = (
        df["return_1d"].rolling(20).std()
    )

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()

    df["ma20_ratio"] = close / ma20 - 1
    df["ma50_ratio"] = close / ma50 - 1

    df["rsi"] = calculate_rsi(close)

    df["volume_change"] = volume.pct_change()

    # What we want to predict
    df["future_return"] = (
        close.shift(-horizon) / close - 1
    )

    df["target"] = (
        df["future_return"] > 0
    ).astype(int)

    df = df.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    df = df.dropna()

    return df


def train_model(df):
    X = df[FEATURES]
    y = df["target"]

    # Chronological split.
    split = int(len(df) * 0.8)

    X_train = X.iloc[:split]
    X_test = X.iloc[split:]

    y_train = y.iloc[:split]
    y_test = y.iloc[split:]

    model = HistGradientBoostingClassifier(
        max_iter=200,
        learning_rate=0.05,
        max_leaf_nodes=15,
        l2_regularization=1.0,
        random_state=42,
    )

    model.fit(X_train, y_train)

    test_predictions = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        test_predictions,
    )

    return model, accuracy


def predict(model, df):
    latest = df[FEATURES].iloc[[-1]]

    probabilities = model.predict_proba(
        latest
    )[0]

    probability_down = probabilities[0]
    probability_up = probabilities[1]

    direction = (
        "UP"
        if probability_up >= 0.5
        else "DOWN"
    )

    return {
        "direction": direction,
        "probability_up": float(probability_up),
        "probability_down": float(probability_down),
    }