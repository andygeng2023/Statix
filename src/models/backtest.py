import numpy as np
import pandas as pd

from sklearn.ensemble import (
    HistGradientBoostingClassifier,
)
from sklearn.metrics import (
    accuracy_score,
)


def walk_forward_backtest(
    data: pd.DataFrame,
    features: list[str],
    target_column: str = "target",
    minimum_train_size: int = 300,
):

    clean = data.replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna(
        subset=features
        + [target_column]
    )

    if len(clean) < minimum_train_size + 30:
        return {
            "accuracy": None,
            "predictions": 0,
            "message": (
                "Not enough history "
                "for backtesting."
            ),
        }

    predictions = []

    actual = []

    step = max(
        20,
        len(clean) // 12,
    )

    for end in range(
        minimum_train_size,
        len(clean),
        step,
    ):

        train = clean.iloc[:end]

        test = clean.iloc[
            end:min(
                end + step,
                len(clean),
            )
        ]

        if test.empty:
            break

        model = (
            HistGradientBoostingClassifier(
                max_iter=100,
                learning_rate=0.06,
                max_leaf_nodes=15,
                random_state=42,
            )
        )

        model.fit(
            train[features],
            train[target_column].astype(int),
        )

        pred = model.predict(
            test[features]
        )

        predictions.extend(
            pred.tolist()
        )

        actual.extend(
            test[target_column]
            .astype(int)
            .tolist()
        )

    if not actual:
        return {
            "accuracy": None,
            "predictions": 0,
            "message": "No test predictions.",
        }

    return {
        "accuracy": float(
            accuracy_score(
                actual,
                predictions,
            )
        ),
        "predictions": len(actual),
        "message": "Completed",
    }