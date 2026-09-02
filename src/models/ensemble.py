import numpy as np

from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, mean_squared_error


MODEL_VERSION = "statix-v6-ensemble-1"

CLASS_NAMES = {
    0: "Strong Bearish",
    1: "Bearish",
    2: "Neutral",
    3: "Bullish",
    4: "Strong Bullish",
}

WEIGHTS = np.array([
    0.45,
    0.35,
    0.20,
])


def _make_classifiers():

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
            n_estimators=260,
            max_depth=12,
            min_samples_leaf=5,
            max_features="sqrt",
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=42,
        ),

        Pipeline([
            (
                "scale",
                StandardScaler()
            ),
            (
                "model",
                LogisticRegression(
                    max_iter=1200,
                    C=0.35,
                    class_weight="balanced",
                    multi_class="auto",
                    random_state=42,
                )
            ),
        ]),
    ]


def _make_regressors():

    return [
        HistGradientBoostingRegressor(
            max_iter=180,
            learning_rate=0.045,
            max_leaf_nodes=15,
            min_samples_leaf=12,
            l2_regularization=2.0,
            loss="huber",
            random_state=42,
        ),

        RandomForestRegressor(
            n_estimators=260,
            max_depth=12,
            min_samples_leaf=5,
            max_features="sqrt",
            n_jobs=-1,
            random_state=42,
        ),

        Pipeline([
            (
                "scale",
                StandardScaler()
            ),
            (
                "model",
                Ridge(alpha=8.0)
            ),
        ]),
    ]


def _probability_matrix(model, X, all_classes):

    probabilities = model.predict_proba(X)

    output = np.zeros(
        (len(X), len(all_classes))
    )

    for i, cls in enumerate(model.classes_):
        position = list(all_classes).index(cls)
        output[:, position] = probabilities[:, i]

    return output


def train_and_predict(
    training_df,
    latest_df,
    feature_columns,
):

    if len(training_df) < 220:
        raise ValueError(
            "Not enough historical feature rows."
        )

    if latest_df.empty:
        raise ValueError(
            "No usable latest feature row."
        )

    X = training_df[feature_columns]
    y = training_df["target"].astype(int)

    y_return = training_df["future_return"]

    # Chronological split.
    split = int(len(X) * 0.82)

    X_train = X.iloc[:split]
    X_test = X.iloc[split:]

    y_train = y.iloc[:split]
    y_test = y.iloc[split:]

    r_train = y_return.iloc[:split]
    r_test = y_return.iloc[split:]

    all_classes = np.array([0, 1, 2, 3, 4])

    classifiers = _make_classifiers()
    regressors = _make_regressors()

    classifier_probabilities = []
    regression_predictions = []

    model_accuracies = []
    model_rmse = []

    for classifier in classifiers:

        classifier.fit(
            X_train,
            y_train,
        )

        probabilities = _probability_matrix(
            classifier,
            X_test,
            all_classes,
        )

        classifier_probabilities.append(
            probabilities
        )

        predictions = all_classes[
            np.argmax(probabilities, axis=1)
        ]

        model_accuracies.append(
            accuracy_score(
                y_test,
                predictions,
            )
        )

    for regressor in regressors:

        regressor.fit(
            X_train,
            r_train,
        )

        predictions = regressor.predict(X_test)

        regression_predictions.append(
            predictions
        )

        model_rmse.append(
            mean_squared_error(
                r_test,
                predictions,
                squared=False,
            )
        )

    # -------------------------
    # Train final models
    # -------------------------

    latest_X = latest_df[
        feature_columns
    ].iloc[[-1]]

    latest_probabilities = []

    final_regression_predictions = []

    for classifier in _make_classifiers():

        classifier.fit(
            X,
            y,
        )

        probabilities = _probability_matrix(
            classifier,
            latest_X,
            all_classes,
        )[0]

        latest_probabilities.append(
            probabilities
        )

    for regressor in _make_regressors():

        regressor.fit(
            X,
            y_return,
        )

        final_regression_predictions.append(
            float(
                regressor.predict(latest_X)[0]
            )
        )

    latest_probabilities = np.array(
        latest_probabilities
    )

    ensemble_probability = (
        latest_probabilities * WEIGHTS[:, None]
    ).sum(axis=0)

    ensemble_probability = (
        ensemble_probability
        / ensemble_probability.sum()
    )

    expected_return = float(
        np.average(
            final_regression_predictions,
            weights=WEIGHTS,
        )
    )

    # -------------------------
    # Signal
    # -------------------------

    up_probability = float(
        ensemble_probability[3]
        + ensemble_probability[4]
    )

    down_probability = float(
        ensemble_probability[0]
        + ensemble_probability[1]
    )

    strongest_class = int(
        np.argmax(ensemble_probability)
    )

    if (
        strongest_class >= 3
        and up_probability >= 0.55
    ):
        direction = "Bullish"

    elif (
        strongest_class <= 1
        and down_probability >= 0.55
    ):
        direction = "Bearish"

    else:
        direction = "Neutral"

    # -------------------------
    # Model agreement
    # -------------------------

    model_up_probabilities = (
        latest_probabilities[:, 3]
        + latest_probabilities[:, 4]
    )

    agreement = float(
        1 - np.std(model_up_probabilities) * 2
    )

    agreement = max(
        0.0,
        min(1.0, agreement),
    )

    # -------------------------
    # Validation
    # -------------------------

    accuracy = float(
        np.average(
            model_accuracies,
            weights=WEIGHTS,
        )
    )

    rmse = float(
        np.average(
            model_rmse,
            weights=WEIGHTS,
        )
    )

    majority_baseline = float(
        y_test.value_counts(
            normalize=True
        ).max()
    )

    improvement = accuracy - majority_baseline

    # -------------------------
    # Confidence
    # -------------------------

    directional_strength = abs(
        up_probability - 0.5
    ) * 2

    confidence = (
        directional_strength * 0.45
        + agreement * 0.30
        + min(accuracy, 1) * 0.25
    )

    confidence = max(
        0.0,
        min(1.0, confidence),
    )

    return {
        "direction": direction,
        "expected_return": expected_return,
        "probability_up": up_probability,
        "probability_down": down_probability,
        "confidence": confidence,
        "agreement": agreement,
        "accuracy": accuracy,
        "baseline_accuracy": majority_baseline,
        "improvement": improvement,
        "rmse": rmse,
        "training_rows": len(X),
        "validation_rows": len(X_test),
        "class_probabilities": {
            CLASS_NAMES[i]: float(
                ensemble_probability[i]
            )
            for i in range(5)
        },
        "model_accuracies": model_accuracies,
        "model_rmse": model_rmse,
    }