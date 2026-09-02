import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


FEATURES = [
    "return_1d",
    "return_5d",
    "return_20d",
    "volatility_20d",
    "ma_ratio",
    "volume_change",
]


def create_features(data, horizon=5):
    df = data.copy()

    # Price changes
    df["return_1d"] = df["Close"].pct_change(1)
    df["return_5d"] = df["Close"].pct_change(5)
    df["return_20d"] = df["Close"].pct_change(20)

    # Volatility
    df["volatility_20d"] = df["return_1d"].rolling(20).std()

    # Moving-average relationship
    ma20 = df["Close"].rolling(20).mean()
    df["ma_ratio"] = df["Close"] / ma20 - 1

    # Volume
    df["volume_change"] = df["Volume"].pct_change()

    # Future return — this is the thing we're trying to predict
    df["future_return"] = (
        df["Close"].shift(-horizon) / df["Close"] - 1
    )

    # 1 = price goes up, 0 = price goes down
    df["target"] = (df["future_return"] > 0).astype(int)

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()

    return df


def train_model(df):
    X = df[FEATURES]
    y = df["target"]

    # IMPORTANT:
    # Do not randomly shuffle stock data.
    # The newest portion is kept completely separate.
    split = int(len(df) * 0.8)

    X_train = X.iloc[:split]
    X_test = X.iloc[split:]

    y_train = y.iloc[:split]
    y_test = y.iloc[split:]

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=5,
        random_state=42,
        class_weight="balanced",
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    return model, accuracy


def predict_next(df, model):
    latest = df[FEATURES].iloc[[-1]]

    probability = model.predict_proba(latest)[0]

    probability_down = probability[0]
    probability_up = probability[1]

    direction = "UP" if probability_up >= 0.5 else "DOWN"

    return {
        "direction": direction,
        "probability_up": probability_up,
        "probability_down": probability_down,
    }