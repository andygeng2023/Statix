import numpy as np

from sklearn.ensemble import (
    RandomForestClassifier,
    HistGradientBoostingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


def train_models(X, y):
    models = {
        "gradient_boosting": HistGradientBoostingClassifier(
            max_iter=250,
            learning_rate=0.04,
            max_leaf_nodes=15,
            l2_regularization=1.5,
            random_state=42,
        ),

        "random_forest": RandomForestClassifier(
            n_estimators=350,
            max_depth=10,
            min_samples_leaf=5,
            max_features="sqrt",
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),

        "logistic": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        C=0.5,
                        max_iter=2000,
                    ),
                ),
            ]
        ),
    }

    for model in models.values():
        model.fit(X, y)

    return models


def ensemble_probability(models, X):
    probabilities = []

    for model in models.values():
        probability = model.predict_proba(X)[:, 1]
        probabilities.append(probability)

    probabilities = np.array(probabilities)

    # Gradient boosting receives slightly more weight.
    weights = np.array([0.40, 0.35, 0.25])

    return np.average(
        probabilities,
        axis=0,
        weights=weights,
    )


def train_and_predict(
    features,
    feature_columns,
):
    data = features.dropna(
        subset=feature_columns + ["target"]
    ).copy()

    if len(data) < 250:
        raise ValueError(
            "Not enough historical data for a reliable model."
        )

    X = data[feature_columns]
    y = data["target"]

    split = int(len(data) * 0.8)

    X_train = X.iloc[:split]
    y_train = y.iloc[:split]

    X_test = X.iloc[split:]
    y_test = y.iloc[split:]

    models = train_models(X_train, y_train)

    test_probability = ensemble_probability(
        models,
        X_test,
    )

    test_predictions = (
        test_probability >= 0.5
    ).astype(int)

    accuracy = float(
        (test_predictions == y_test.values).mean()
    )

    latest = features.dropna(
        subset=feature_columns
    ).iloc[[-1]]

    latest_probability = float(
        ensemble_probability(
            models,
            latest[feature_columns],
        )[0]
    )

    # Estimate expected return from historical outcomes
    positive_returns = data.loc[
        data["target"] == 1,
        "future_return",
    ]

    negative_returns = data.loc[
        data["target"] == 0,
        "future_return",
    ]

    avg_positive = (
        float(positive_returns.mean())
        if len(positive_returns)
        else 0
    )

    avg_negative = (
        float(negative_returns.mean())
        if len(negative_returns)
        else 0
    )

    expected_return = (
        latest_probability * avg_positive
        + (1 - latest_probability) * avg_negative
    )

    if latest_probability >= 0.55:
        direction = "Bullish"
    elif latest_probability <= 0.45:
        direction = "Bearish"
    else:
        direction = "Neutral"

    confidence = abs(
        latest_probability - 0.5
    ) * 2

    return {
        "direction": direction,
        "probability_up": latest_probability,
        "probability_down": 1 - latest_probability,
        "expected_return": expected_return,
        "confidence": confidence,
        "test_accuracy": accuracy,
        "models": models,
    }