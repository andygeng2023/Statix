from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

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
from sklearn.metrics import (
    accuracy_score,
    mean_squared_error,
)


MODEL_VERSION = "statix-v6-ensemble-2"

CLASS_NAMES = [
    "Strong Bearish",
    "Bearish",
    "Neutral",
    "Bullish",
    "Strong Bullish",
]


def _clean_features(
    df: pd.DataFrame,
    feature_columns: list[str],
) -> pd.DataFrame:
    """
    Convert model features to numeric values and remove
    problematic infinite values.
    """

    X = df[feature_columns].copy()

    for column in feature_columns:
        X[column] = pd.to_numeric(
            X[column],
            errors="coerce",
        )

    X = X.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    # Features should already have been cleaned by create_features().
    # Zero is a safe final fallback for any remaining numerical gaps.
    X = X.fillna(0.0)

    return X.astype(float)


def _clean_target(
    series: pd.Series,
) -> pd.Series:
    y = pd.to_numeric(
        series,
        errors="coerce",
    )

    return y.astype(int)


def _make_classifiers() -> list[Any]:
    """
    Three deliberately different classifiers.

    No multi_class parameter is supplied to LogisticRegression.
    This keeps the implementation compatible with current
    scikit-learn versions.
    """

    return [
        HistGradientBoostingClassifier(
            max_iter=180,
            learning_rate=0.045,
            max_leaf_nodes=15,
            min_samples_leaf=12,
            l2_regularization=2.0,
            random_state=42,
        ),
        RandomForestClassifier(
            n_estimators=250,
            max_depth=10,
            min_samples_leaf=4,
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1,
        ),
        LogisticRegression(
            solver="lbfgs",
            max_iter=2000,
            C=0.7,
            random_state=42,
        ),
    ]


def _make_regressors() -> list[Any]:
    return [
        HistGradientBoostingRegressor(
            max_iter=180,
            learning_rate=0.045,
            max_leaf_nodes=15,
            min_samples_leaf=12,
            l2_regularization=2.0,
            loss="squared_error",
            random_state=42,
        ),
        RandomForestRegressor(
            n_estimators=250,
            max_depth=10,
            min_samples_leaf=4,
            max_features="sqrt",
            random_state=42,
            n_jobs=-1,
        ),
        Ridge(
            alpha=10.0,
        ),
    ]


def _probability_matrix(
    model: Any,
    X: pd.DataFrame,
) -> np.ndarray:
    """
    Return probabilities in the fixed five-class order.

    A classifier may not see every class in a particular training
    split, so its probability columns have to be aligned.
    """

    probabilities = model.predict_proba(X)

    classes = getattr(
        model,
        "classes_",
        np.arange(probabilities.shape[1]),
    )

    aligned = np.zeros(
        (len(X), len(CLASS_NAMES)),
        dtype=float,
    )

    for index, class_value in enumerate(classes):
        try:
            class_index = int(class_value)
        except Exception:
            continue

        if 0 <= class_index < len(CLASS_NAMES):
            aligned[:, class_index] = probabilities[
                :, index
            ]

    row_sums = aligned.sum(axis=1)

    valid = row_sums > 0

    aligned[valid] = (
        aligned[valid]
        / row_sums[valid, None]
    )

    return aligned


def _walk_forward_validation(
    X: pd.DataFrame,
    y: pd.Series,
    min_train: int = 180,
    test_size: int = 30,
    step: int = 30,
) -> dict[str, Any]:
    """
    Chronological walk-forward validation.

    No future rows are used to train earlier predictions.
    """

    records: list[dict[str, Any]] = []

    if len(X) < min_train + test_size:
        return {
            "accuracy": None,
            "baseline": None,
            "folds": 0,
        }

    start = min_train
    folds = 0

    while start + test_size <= len(X):
        train_end = start
        test_end = start + test_size

        X_train = X.iloc[:train_end]
        y_train = y.iloc[:train_end]

        X_test = X.iloc[
            train_end:test_end
        ]
        y_test = y.iloc[
            train_end:test_end
        ]

        if y_train.nunique() < 2:
            start += step
            continue

        model = HistGradientBoostingClassifier(
            max_iter=120,
            learning_rate=0.05,
            max_leaf_nodes=12,
            min_samples_leaf=10,
            l2_regularization=2.0,
            random_state=42,
        )

        try:
            model.fit(
                X_train,
                y_train,
            )

            predictions = model.predict(
                X_test
            )

        except Exception:
            start += step
            continue

        for date, actual, predicted in zip(
            y_test.index,
            y_test,
            predictions,
        ):
            records.append(
                {
                    "date": date,
                    "actual": int(actual),
                    "predicted": int(predicted),
                }
            )

        folds += 1
        start += step

    if not records:
        return {
            "accuracy": None,
            "baseline": None,
            "folds": 0,
        }

    validation = pd.DataFrame(records)

    accuracy = accuracy_score(
        validation["actual"],
        validation["predicted"],
    )

    baseline = float(
        y.iloc[:min_train]
        .value_counts(
            normalize=True
        )
        .max()
    )

    return {
        "accuracy": float(accuracy),
        "baseline": baseline,
        "folds": folds,
    }


def _calculate_confidence(
    probabilities: np.ndarray,
    model_agreement: float,
) -> float:
    """
    Combine prediction strength and ensemble agreement.

    This is a model confidence score, not a probability that
    the prediction will be correct.
    """

    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    if probabilities.size == 0:
        return 0.0

    top_probability = float(
        np.max(probabilities)
    )

    # Convert probability concentration into a 0-1 strength score.
    # Uniform five-class probability = 0.
    # 100% on one class = 1.
    class_count = len(CLASS_NAMES)

    chance = 1.0 / class_count

    if top_probability <= chance:
        probability_strength = 0.0
    else:
        probability_strength = (
            top_probability - chance
        ) / (1.0 - chance)

    confidence = (
        0.65 * probability_strength
        + 0.35 * model_agreement
    )

    return float(
        np.clip(
            confidence,
            0.0,
            1.0,
        )
    )


def train_and_predict(
    training_df: pd.DataFrame,
    latest_df: pd.DataFrame,
    feature_columns: list[str],
) -> dict[str, Any]:
    """
    Train the Statix ensemble and generate one latest prediction.

    Returns a dictionary designed to work directly with:
        pages/prediction.py
        storage/database.py
        pages/watchlist.py
    """

    if training_df is None or training_df.empty:
        raise ValueError(
            "No training data is available."
        )

    if latest_df is None or latest_df.empty:
        raise ValueError(
            "No latest feature row is available."
        )

    if not feature_columns:
        raise ValueError(
            "No model features were supplied."
        )

    required_training = (
        set(feature_columns)
        | {"target", "future_return"}
    )

    missing_training = [
        column
        for column in required_training
        if column not in training_df.columns
    ]

    if missing_training:
        raise ValueError(
            "Training data is missing: "
            + ", ".join(missing_training)
        )

    missing_latest = [
        column
        for column in feature_columns
        if column not in latest_df.columns
    ]

    if missing_latest:
        raise ValueError(
            "Latest prediction row is missing: "
            + ", ".join(missing_latest)
        )

    X = _clean_features(
        training_df,
        feature_columns,
    )

    X_latest = _clean_features(
        latest_df,
        feature_columns,
    )

    y = _clean_target(
        training_df["target"]
    )

    future_return = pd.to_numeric(
        training_df["future_return"],
        errors="coerce",
    )

    valid = future_return.notna()

    X = X.loc[valid]
    y = y.loc[valid]
    future_return = future_return.loc[valid]

    if len(X) < 180:
        raise ValueError(
            f"Only {len(X)} usable training rows are available. "
            "At least 180 are required."
        )

    if y.nunique() < 2:
        raise ValueError(
            "The training target contains fewer than two classes."
        )

    # -----------------------------------------------------
    # Walk-forward validation
    # -----------------------------------------------------

    validation = _walk_forward_validation(
        X,
        y,
        min_train=180,
        test_size=30,
        step=30,
    )

    # -----------------------------------------------------
    # Classification ensemble
    # -----------------------------------------------------

    classifiers = _make_classifiers()

    probability_predictions: list[np.ndarray] = []
    class_predictions: list[int] = []

    for model in classifiers:
        try:
            model.fit(
                X,
                y,
            )

            probabilities = _probability_matrix(
                model,
                X_latest,
            )[0]

            prediction = int(
                np.argmax(probabilities)
            )

            probability_predictions.append(
                probabilities
            )

            class_predictions.append(
                prediction
            )

        except Exception as exc:
            raise RuntimeError(
                f"Classifier training failed: "
                f"{type(model).__name__}: {exc}"
            ) from exc

    if not probability_predictions:
        raise RuntimeError(
            "No classification model produced a prediction."
        )

    probability_matrix = np.vstack(
        probability_predictions
    )

    average_probabilities = (
        probability_matrix.mean(axis=0)
    )

    # Normalize again to eliminate floating-point drift.
    probability_sum = (
        average_probabilities.sum()
    )

    if probability_sum > 0:
        average_probabilities = (
            average_probabilities
            / probability_sum
        )

    predicted_class = int(
        np.argmax(
            average_probabilities
        )
    )

    signal = CLASS_NAMES[
        predicted_class
    ]

    # -----------------------------------------------------
    # Model agreement
    # -----------------------------------------------------

    model_agreement = float(
        np.mean(
            np.asarray(class_predictions)
            == predicted_class
        )
    )

    # -----------------------------------------------------
    # Probability up
    #
    # Classes 3 and 4 are bullish.
    # Class 2 is neutral.
    # Classes 0 and 1 are bearish.
    # -----------------------------------------------------

    probability_up = float(
        average_probabilities[3]
        + average_probabilities[4]
    )

    # -----------------------------------------------------
    # Regression ensemble
    # -----------------------------------------------------

    regressors = _make_regressors()

    regression_predictions: list[float] = []

    for model in regressors:
        try:
            model.fit(
                X,
                future_return,
            )

            prediction = float(
                model.predict(
                    X_latest
                )[0]
            )

            regression_predictions.append(
                prediction
            )

        except Exception as exc:
            raise RuntimeError(
                f"Regression training failed: "
                f"{type(model).__name__}: {exc}"
            ) from exc

    if not regression_predictions:
        raise RuntimeError(
            "No regression model produced a prediction."
        )

    expected_return = float(
        np.mean(
            regression_predictions
        )
    )

    # Avoid allowing a pathological model output to explode
    # the UI. This is only a display/trust safeguard.
    expected_return = float(
        np.clip(
            expected_return,
            -1.0,
            1.0,
        )
    )

    # -----------------------------------------------------
    # Confidence
    # -----------------------------------------------------

    confidence = _calculate_confidence(
        average_probabilities,
        model_agreement,
    )

    # -----------------------------------------------------
    # Training error / RMSE
    #
    # This is deliberately reported as training RMSE.
    # The classification metric above is walk-forward validation.
    # -----------------------------------------------------

    regression_train_predictions = []

    for model in regressors:
        prediction = model.predict(X)
        regression_train_predictions.append(
            np.asarray(prediction)
        )

    average_regression_training = np.mean(
        np.vstack(
            regression_train_predictions
        ),
        axis=0,
    )

    rmse = float(
        np.sqrt(
            mean_squared_error(
                future_return,
                average_regression_training,
            )
        )
    )

    # -----------------------------------------------------
    # Result
    # -----------------------------------------------------

    return {
        "signal": signal,
        "probability_up": probability_up,
        "expected_return": expected_return,
        "confidence": confidence,

        "class_probabilities": {
            CLASS_NAMES[index]: float(
                average_probabilities[index]
            )
            for index in range(
                len(CLASS_NAMES)
            )
        },

        "model_agreement": model_agreement,

        "validation_accuracy": validation[
            "accuracy"
        ],

        "baseline_accuracy": validation[
            "baseline"
        ],

        "validation_folds": validation[
            "folds"
        ],

        "training_rows": int(
            len(X)
        ),

        "feature_count": int(
            len(feature_columns)
        ),

        "rmse": rmse,

        "model_version": MODEL_VERSION,
    }