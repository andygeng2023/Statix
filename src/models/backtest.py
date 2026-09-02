from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
)

from .ensemble import train_models, ensemble_probability


def run_backtest(
    features,
    feature_columns,
    train_ratio=0.7,
):
    data = features.dropna(
        subset=feature_columns + ["target"]
    ).copy()

    split = int(len(data) * train_ratio)

    train = data.iloc[:split]
    test = data.iloc[split:]

    models = train_models(
        train[feature_columns],
        train["target"],
    )

    probabilities = ensemble_probability(
        models,
        test[feature_columns],
    )

    predictions = (
        probabilities >= 0.5
    ).astype(int)

    actual = test["target"].values

    return {
        "accuracy": accuracy_score(
            actual,
            predictions,
        ),
        "precision": precision_score(
            actual,
            predictions,
            zero_division=0,
        ),
        "recall": recall_score(
            actual,
            predictions,
            zero_division=0,
        ),
        "samples": len(test),
    }