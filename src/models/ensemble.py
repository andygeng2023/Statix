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
from sklearn.metrics import (
    accuracy_score,
    mean_squared_error,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


MODEL_VERSION = "statix-v6.1-ensemble"

CLASS_NAMES = {
    0: "Strong Bearish",
    1: "Bearish",
    2: "Neutral",
    3: "Bullish",
    4: "Strong Bullish",
}

WEIGHTS = np.array(
    [
        0.45,
        0.35,
        0.20,
    ]
)


def make_classifiers():

    return [
        HistGradientBoostingClassifier(
            max_iter=160,
            learning_rate=0.045,
            max_leaf_nodes=15,
            min_samples_leaf=12,
            l2_regularization=2.0,
            random_state=42,
        ),

        RandomForestClassifier(
            n_estimators=220,
            max_depth=12,
            min_samples_leaf=5,
            max_features="sqrt",
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=42,
        ),

        Pipeline(
            [
                (
                    "scale",
                    StandardScaler(),
                ),
                (
                    "model",
                    LogisticRegression(
                        max_iter=800,
                        C=0.35,
                        class_weight="balanced",
                        solver="lbfgs",
                        random_state=42,
                    ),
                ),
            ]
        ),
    ]


def make_regressors():

    return [
        HistGradientBoostingRegressor(
            max_iter=160,
            learning_rate=0.045,
            max_leaf_nodes=15,
            min_samples_leaf=12,
            l2_regularization=2.0,
            loss="huber",
            random_state=42,
        ),

        RandomForestRegressor(
            n_estimators=220,
            max_depth=12,
            min_samples_leaf=5,
            max_features="sqrt",
            n_jobs=-1,
            random_state=42,
        ),

        Pipeline(
            [
                (
                    "scale",
                    StandardScaler(),
                ),
                (
                    "model",
                    Ridge(alpha=8.0),
                ),
            ]
        ),
    ]


def align_probabilities(
    model,
    X,
):

    raw = model.predict_proba(X)

    output = np.zeros(
        (
            len(X),
            5,
        )
    )

    for index, cls in enumerate(
        model.classes_
    ):

        cls = int(cls)

        if 0 <= cls <= 4:

            output[
                :,
                cls,
            ] = raw[
                :,
                index,
            ]

    row_sums = output.sum(
        axis=1,
        keepdims=True,
    )

    row_sums[
        row_sums == 0
    ] = 1

    return output / row_sums


def train_and_predict(
    training_df,
    latest_df,
    feature_columns,
):

    if len(training_df) < 220:

        raise ValueError(
            "At least 220 usable historical rows are required."
        )

    if latest_df.empty:

        raise ValueError(
            "No usable latest feature row exists."
        )

    X = training_df[
        feature_columns
    ].astype(float)

    y = (
        training_df["target"]
        .astype(int)
    )

    future_returns = (
        training_df["future_return"]
        .astype(float)
    )

    # Remove any remaining invalid numeric values.
    X = X.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    valid_rows = X.notna().all(
        axis=1
    )

    X = X.loc[valid_rows]
    y = y.loc[valid_rows]
    future_returns = (
        future_returns
        .loc[valid_rows]
    )

    if y.nunique() < 2:

        raise ValueError(
            "The historical data contains only one target class."
        )

    split = int(
        len(X) * 0.82
    )

    X_train = X.iloc[:split]
    X_test = X.iloc[split:]

    y_train = y.iloc[:split]
    y_test = y.iloc[split:]

    returns_train = (
        future_returns.iloc[:split]
    )

    returns_test = (
        future_returns.iloc[split:]
    )

    if y_train.nunique() < 2:

        raise ValueError(
            "The training period does not contain enough target classes."
        )

    classifiers = make_classifiers()
    regressors = make_regressors()

    test_probabilities = []
    classifier_accuracies = []

    for model in classifiers:

        model.fit(
            X_train,
            y_train,
        )

        probabilities = (
            align_probabilities(
                model,
                X_test,
            )
        )

        test_probabilities.append(
            probabilities
        )

        predicted = np.argmax(
            probabilities,
            axis=1,
        )

        classifier_accuracies.append(
            accuracy_score(
                y_test,
                predicted,
            )
        )

    regression_predictions = []
    regression_errors = []

    for model in regressors:

        model.fit(
            X_train,
            returns_train,
        )

        predicted = model.predict(
            X_test
        )

        regression_predictions.append(
            predicted
        )

        regression_errors.append(
            mean_squared_error(
                returns_test,
                predicted,
                squared=False,
            )
        )

    # -------------------------
    # Final models
    # -------------------------

    latest_X = (
        latest_df[
            feature_columns
        ]
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .ffill()
        .bfill()
        .fillna(0)
        .astype(float)
        .iloc[[-1]]
    )

    latest_probabilities = []

    for model in make_classifiers():

        model.fit(
            X,
            y,
        )

        probabilities = (
            align_probabilities(
                model,
                latest_X,
            )[0]
        )

        latest_probabilities.append(
            probabilities
        )

    latest_returns = []

    for model in make_regressors():

        model.fit(
            X,
            future_returns,
        )

        latest_returns.append(
            float(
                model.predict(
                    latest_X
                )[0]
            )
        )

    latest_probabilities = np.asarray(
        latest_probabilities
    )

    ensemble_probabilities = (
        latest_probabilities
        * WEIGHTS[:, None]
    ).sum(axis=0)

    ensemble_probabilities /= (
        ensemble_probabilities.sum()
    )

    expected_return = float(
        np.average(
            latest_returns,
            weights=WEIGHTS,
        )
    )

    probability_up = float(
        ensemble_probabilities[3]
        + ensemble_probabilities[4]
    )

    probability_down = float(
        ensemble_probabilities[0]
        + ensemble_probabilities[1]
    )

    strongest_class = int(
        np.argmax(
            ensemble_probabilities
        )
    )

    if (
        strongest_class == 4
        and probability_up >= 0.60
    ):

        direction = "Bullish"

    elif (
        strongest_class >= 3
        and probability_up >= 0.55
    ):

        direction = "Bullish"

    elif (
        strongest_class == 0
        and probability_down >= 0.60
    ):

        direction = "Bearish"

    elif (
        strongest_class <= 1
        and probability_down >= 0.55
    ):

        direction = "Bearish"

    else:

        direction = "Neutral"

    # -------------------------
    # Agreement
    # -------------------------

    model_up_probabilities = (
        latest_probabilities[:, 3]
        + latest_probabilities[:, 4]
    )

    agreement = (
        1
        - np.std(
            model_up_probabilities
        ) * 2
    )

    agreement = float(
        np.clip(
            agreement,
            0,
            1,
        )
    )

    # -------------------------
    # Validation
    # -------------------------

    accuracy = float(
        np.average(
            classifier_accuracies,
            weights=WEIGHTS,
        )
    )

    rmse = float(
        np.average(
            regression_errors,
            weights=WEIGHTS,
        )
    )

    baseline = float(
        y_test.value_counts(
            normalize=True
        ).max()
    )

    improvement = (
        accuracy - baseline
    )

    directional_strength = (
        abs(
            probability_up - 0.5
        ) * 2
    )

    confidence = (
        directional_strength * 0.45
        + agreement * 0.30
        + accuracy * 0.25
    )

    confidence = float(
        np.clip(
            confidence,
            0,
            1,
        )
    )

    return {
        "direction": direction,
        "expected_return": expected_return,
        "probability_up": probability_up,
        "probability_down": probability_down,
        "confidence": confidence,
        "agreement": agreement,
        "accuracy": accuracy,
        "baseline_accuracy": baseline,
        "improvement": improvement,
        "rmse": rmse,
        "training_rows": len(X),
        "validation_rows": len(X_test),
        "class_probabilities": {
            CLASS_NAMES[i]: float(
                ensemble_probabilities[i]
            )
            for i in range(5)
        },
        "model_accuracies": (
            classifier_accuracies
        ),
        "model_rmse": regression_errors,
    }