import numpy as np

from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)

from sklearn.linear_model import (
    LogisticRegression,
    Ridge,
)

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


MODEL_VERSION = "statix-v4-ensemble-1"


def train_classifier_models(
    X,
    y,
):
    models = {
        "gradient_boosting": (
            HistGradientBoostingClassifier(
                max_iter=250,
                learning_rate=0.035,
                max_leaf_nodes=15,
                l2_regularization=1.5,
                random_state=42,
            )
        ),

        "random_forest": (
            RandomForestClassifier(
                n_estimators=400,
                max_depth=10,
                min_samples_leaf=5,
                max_features="sqrt",
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            )
        ),

        "logistic": Pipeline(
            [
                (
                    "scaler",
                    StandardScaler(),
                ),
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


def train_regression_models(
    X,
    y,
):
    models = {
        "gradient_boosting": (
            HistGradientBoostingRegressor(
                max_iter=250,
                learning_rate=0.035,
                max_leaf_nodes=15,
                l2_regularization=1.5,
                random_state=42,
            )
        ),

        "random_forest": (
            RandomForestRegressor(
                n_estimators=350,
                max_depth=10,
                min_samples_leaf=5,
                max_features="sqrt",
                random_state=42,
                n_jobs=-1,
            )
        ),

        "ridge": Pipeline(
            [
                (
                    "scaler",
                    StandardScaler(),
                ),
                (
                    "model",
                    Ridge(alpha=10.0),
                ),
            ]
        ),
    }

    for model in models.values():
        model.fit(X, y)

    return models


def weighted_probability(
    models,
    X,
):
    probabilities = []

    for model in models.values():
        probabilities.append(
            model.predict_proba(X)[:, 1]
        )

    probabilities = np.array(
        probabilities
    )

    weights = np.array(
        [
            0.40,
            0.35,
            0.25,
        ]
    )

    return np.average(
        probabilities,
        axis=0,
        weights=weights,
    )


def weighted_return(
    models,
    X,
):
    predictions = []

    for model in models.values():
        predictions.append(
            model.predict(X)
        )

    predictions = np.array(
        predictions
    )

    weights = np.array(
        [
            0.40,
            0.35,
            0.25,
        ]
    )

    return np.average(
        predictions,
        axis=0,
        weights=weights,
    )


def train_and_predict(
    features,
    feature_columns,
    horizon=5,
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
            "At least 250 usable historical "
            "observations are recommended."
        )

    X = data[feature_columns]

    y_classification = data[
        "target"
    ]

    y_return = data[
        "future_return"
    ]

    split = int(
        len(data) * 0.80
    )

    X_train = X.iloc[:split]
    X_test = X.iloc[split:]

    y_class_train = (
        y_classification.iloc[:split]
    )

    y_class_test = (
        y_classification.iloc[split:]
    )

    y_return_train = (
        y_return.iloc[:split]
    )

    y_return_test = (
        y_return.iloc[split:]
    )

    if y_class_train.nunique() < 2:
        raise ValueError(
            "Historical data does not contain "
            "enough variation for classification."
        )

    classifier_models = (
        train_classifier_models(
            X_train,
            y_class_train,
        )
    )

    regression_models = (
        train_regression_models(
            X_train,
            y_return_train,
        )
    )

    # Classification evaluation
    test_probability = (
        weighted_probability(
            classifier_models,
            X_test,
        )
    )

    test_predictions = (
        test_probability >= 0.5
    ).astype(int)

    accuracy = float(
        (
            test_predictions
            == y_class_test.to_numpy()
        ).mean()
    )

    # Regression evaluation
    test_return_prediction = (
        weighted_return(
            regression_models,
            X_test,
        )
    )

    if len(y_return_test) > 1:
        return_errors = (
            test_return_prediction
            - y_return_test.to_numpy()
        )

        rmse = float(
            np.sqrt(
                np.mean(
                    return_errors ** 2
                )
            )
        )
    else:
        rmse = 0.0

    # Latest observation
    latest = features.dropna(
        subset=feature_columns
    ).iloc[[-1]]

    probability_up = float(
        weighted_probability(
            classifier_models,
            latest[feature_columns],
        )[0]
    )

    expected_return = float(
        weighted_return(
            regression_models,
            latest[feature_columns],
        )[0]
    )

    if probability_up >= 0.55:
        direction = "Bullish"
    elif probability_up <= 0.45:
        direction = "Bearish"
    else:
        direction = "Neutral"

    confidence = abs(
        probability_up - 0.5
    ) * 2

    return {
        "model_version": MODEL_VERSION,
        "horizon": horizon,
        "direction": direction,
        "probability_up": probability_up,
        "probability_down": (
            1 - probability_up
        ),
        "expected_return": expected_return,
        "confidence": confidence,
        "test_accuracy": accuracy,
        "return_rmse": rmse,
    }