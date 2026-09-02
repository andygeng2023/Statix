import numpy as np

from sklearn.metrics import (
    mean_squared_error,
)

from .ensemble import (
    train_classifier_models,
    train_regression_models,
    weighted_probability,
    weighted_return,
)


def run_backtest(
    features,
    feature_columns,
    train_ratio=0.70,
):
    data = features.dropna(
        subset=feature_columns
        + [
            "target",
            "future_return",
        ]
    ).copy()

    if len(data) < 250:
        raise ValueError(
            "Not enough data for backtesting."
        )

    split = int(
        len(data) * train_ratio
    )

    train = data.iloc[:split]
    test = data.iloc[split:]

    classifier_models = (
        train_classifier_models(
            train[feature_columns],
            train["target"],
        )
    )

    regression_models = (
        train_regression_models(
            train[feature_columns],
            train["future_return"],
        )
    )

    probabilities = (
        weighted_probability(
            classifier_models,
            test[feature_columns],
        )
    )

    predictions = (
        probabilities >= 0.5
    ).astype(int)

    actual_direction = (
        test["target"].to_numpy()
    )

    accuracy = float(
        (
            predictions
            == actual_direction
        ).mean()
    )

    predicted_returns = (
        weighted_return(
            regression_models,
            test[feature_columns],
        )
    )

    actual_returns = (
        test[
            "future_return"
        ].to_numpy()
    )

    rmse = float(
        np.sqrt(
            mean_squared_error(
                actual_returns,
                predicted_returns,
            )
        )
    )

    return {
        "accuracy": accuracy,
        "return_rmse": rmse,
        "samples": len(test),
    }