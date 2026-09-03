import pandas as pd

from sklearn.ensemble import (
    HistGradientBoostingClassifier,
)

from sklearn.metrics import (
    accuracy_score,
)


def walk_forward_backtest(
    training_df,
    feature_columns,
    min_train=180,
    test_size=30,
    step=30,
):

    required_rows = (
        min_train
        + test_size
    )

    if len(training_df) < required_rows:

        return {
            "accuracy": None,
            "baseline": None,
            "predictions": pd.DataFrame(),
        }

    X = (
        training_df[
            feature_columns
        ]
        .replace(
            [
                float("inf"),
                -float("inf"),
            ],
            float("nan"),
        )
        .ffill()
        .bfill()
        .fillna(0)
    )

    y = (
        training_df["target"]
        .astype(int)
    )

    records = []

    start = min_train

    while (
        start + test_size
        <= len(training_df)
    ):

        train_end = start
        test_end = (
            start + test_size
        )

        X_train = X.iloc[
            :train_end
        ]

        y_train = y.iloc[
            :train_end
        ]

        X_test = X.iloc[
            train_end:test_end
        ]

        y_test = y.iloc[
            train_end:test_end
        ]

        if y_train.nunique() < 2:

            start += step
            continue

        model = (
            HistGradientBoostingClassifier(
                max_iter=100,
                learning_rate=0.05,
                max_leaf_nodes=12,
                min_samples_leaf=10,
                l2_regularization=2,
                random_state=42,
            )
        )

        model.fit(
            X_train,
            y_train,
        )

        predicted = model.predict(
            X_test
        )

        for date, actual, pred in zip(
            training_df.index[
                train_end:test_end
            ],
            y_test,
            predicted,
        ):

            records.append(
                {
                    "date": date,
                    "actual": int(
                        actual
                    ),
                    "predicted": int(
                        pred
                    ),
                }
            )

        start += step

    result = pd.DataFrame(
        records
    )

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

    baseline = float(
        y.iloc[:min_train]
        .value_counts(
            normalize=True
        )
        .max()
    )

    return {
        "accuracy": float(
            accuracy
        ),
        "baseline": baseline,
        "predictions": result,
    }