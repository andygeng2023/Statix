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


def walk_forward_backtest(
    df,
    horizon=5,
    initial_training_size=250,
):
    """
    Walk-forward backtest.

    At each step:
        1. Train using data available up to that date.
        2. Predict the next observation.
        3. Move forward one observation.
    """

    results = []

    if len(df) <= initial_training_size:
        raise ValueError(
            "Not enough historical data for backtesting."
        )

    for i in range(initial_training_size, len(df)):
        train = df.iloc[:i]
        test = df.iloc[[i]]

        X_train = train[FEATURES]
        y_train = train["target"]

        X_test = test[FEATURES]
        y_test = test["target"]

        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=8,
            min_samples_leaf=5,
            random_state=42,
            class_weight="balanced",
        )

        model.fit(X_train, y_train)

        prediction = model.predict(X_test)[0]
        probability = model.predict_proba(X_test)[0][1]

        results.append({
            "date": test.index[0],
            "actual": int(y_test.iloc[0]),
            "prediction": int(prediction),
            "probability_up": probability,
        })

    results = pd.DataFrame(results)

    accuracy = accuracy_score(
        results["actual"],
        results["prediction"],
    )

    return results, accuracy