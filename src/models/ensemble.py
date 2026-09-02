import numpy as np

from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, mean_squared_error


MODEL_VERSION = "statix-v5-ensemble-1"

WEIGHTS = np.array([0.40, 0.35, 0.25])


def train_and_predict(
    features,
    feature_columns,
    horizon=5,
):
    if features.empty:
        raise ValueError("No usable historical data was produced.")

    required = feature_columns + ["target", "future_return"]

    data = features.dropna(subset=required).copy()

    if len(data) < 180:
        raise ValueError(
            f"Only {len(data)} usable historical rows are available. "
            "At least 180 are required."
        )

    # Make sure both target classes exist.
    if data["target"].nunique() < 2:
        raise ValueError(
            "Historical data does not contain enough variation "
            "to train the prediction model."
        )

    X = data[feature_columns]
    y = data["target"]
    y_return = data["future_return"]

    split = int(len(data) * 0.80)

    if split < 100 or len(data) - split < 30:
        raise ValueError("Not enough historical data for validation.")

    X_train = X.iloc[:split]
    X_test = X.iloc[split:]

    y_train = y.iloc[:split]
    y_test = y.iloc[split:]

    r_train = y_return.iloc[:split]
    r_test = y_return.iloc[split:]

    # -----------------------------
    # Classification models
    # -----------------------------

    classifier_1 = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.035,
        max_leaf_nodes=15,
        l2_regularization=1.5,
        random_state=42,
    )

    classifier_2 = RandomForestClassifier(
        n_estimators=500,
        max_depth=12,
        min_samples_leaf=5,
        max_features="sqrt",
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    classifier_3 = make_pipeline(
        StandardScaler(),
        LogisticRegression(
            max_iter=2000,
            C=0.5,
            random_state=42,
        ),
    )

    classifiers = [
        classifier_1,
        classifier_2,
        classifier_3,
    ]

    probabilities = []

    for model in classifiers:
        model.fit(X_train, y_train)
        probabilities.append(
            model.predict_proba(X_test)[:, 1]
        )

    test_probability = np.average(
        np.vstack(probabilities),
        axis=0,
        weights=WEIGHTS,
    )

    test_prediction = (test_probability >= 0.5).astype(int)

    accuracy = accuracy_score(
        y_test,
        test_prediction,
    )

    # -----------------------------
    # Regression models
    # -----------------------------

    regressor_1 = HistGradientBoostingRegressor(
        max_iter=300,
        learning_rate=0.035,
        max_leaf_nodes=15,
        l2_regularization=1.5,
        random_state=42,
    )

    regressor_2 = RandomForestRegressor(
        n_estimators=500,
        max_depth=12,
        min_samples_leaf=5,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1,
    )

    regressor_3 = make_pipeline(
        StandardScaler(),
        Ridge(alpha=5.0),
    )

    regressors = [
        regressor_1,
        regressor_2,
        regressor_3,
    ]

    return_predictions = []

    for model in regressors:
        model.fit(X_train, r_train)

        return_predictions.append(
            model.predict(X_test)
        )

    test_return = np.average(
        np.vstack(return_predictions),
        axis=0,
        weights=WEIGHTS,
    )

    rmse = float(
        np.sqrt(
            mean_squared_error(
                r_test,
                test_return,
            )
        )
    )

    # -----------------------------
    # Latest prediction
    # -----------------------------

    latest = X.iloc[[-1]]

    latest_probabilities = []

    for model in classifiers:
        latest_probabilities.append(
            model.predict_proba(latest)[:, 1][0]
        )

    probability_up = float(
        np.average(
            latest_probabilities,
            weights=WEIGHTS,
        )
    )

    latest_returns = []

    for model in regressors:
        latest_returns.append(
            float(model.predict(latest)[0])
        )

    expected_return = float(
        np.average(
            latest_returns,
            weights=WEIGHTS,
        )
    )

    if probability_up >= 0.55:
        direction = "Bullish"
    elif probability_up <= 0.45:
        direction = "Bearish"
    else:
        direction = "Neutral"

    confidence = abs(probability_up - 0.5) * 2

    return {
        "model_version": MODEL_VERSION,
        "horizon": horizon,
        "direction": direction,
        "probability_up": probability_up,
        "expected_return": expected_return,
        "confidence": confidence,
        "test_accuracy": float(accuracy),
        "return_rmse": rmse,
        "training_rows": len(X_train),
        "validation_rows": len(X_test),
    }