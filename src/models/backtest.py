import numpy as np
import pandas as pd

from sklearn.metrics import accuracy_score


def walk_forward_backtest(
    training_df,
    feature_columns,
    min_train=180,
    test_size=30,
    step=30,
):

    if len(training_df) < min_train + test_size:
        return {
            "accuracy": None,
            "baseline": None,
            "predictions": pd.DataFrame(),
        }

    X = training_df[feature_columns]
    y = training_df["target"].astype(int)

    records = []

    start = min_train

    while start + test_size <= len(training_df):

        train_end = start
        test_end = start + test_size

        X_train = X.iloc[:train_end]
        y_train = y.iloc[:train_end]

        X_test = X.iloc[train_end:test_end]
        y_test = y.iloc[train_end:test_end]

        from sklearn.ensemble import (
            HistGradientBoostingClassifier,
        )

        model = HistGradientBoostingClassifier(
            max_iter=120,
            learning_rate=0.05,
            max_leaf_nodes=12,
            min_samples_leaf=10,
            l2_regularization=2,
            random_state=42,
        )

        model.fit(
            X_train,
            y_train,
        )

        prediction = model.predict(X_test)

        for date, actual, predicted in zip(
            training_df.index[
                train_end:test_end
            ],
            y_test,
            prediction,
        ):
            records.append(
                {
                    "date": date,
                    "actual": int(actual),
                    "predicted": int(predicted),
                }
            )

        start += step

    result = pd.DataFrame(records)

    if result.empty:
        return {
            "accuracy": None,
            "baseline": None,
            "predictions": result,
        }

    accuracy = accuracy_score(
        result["actual"],
        result["predicted"],
    )

    baseline = (
        y.iloc[:min_train]
        .value_counts(normalize=True)
        .max()
    )

    return {
        "accuracy": float(accuracy),
        "baseline": float(baseline),
        "predictions": result,
    }