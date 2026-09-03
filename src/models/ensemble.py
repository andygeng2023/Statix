from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
)
from sklearn.linear_model import (
    LogisticRegression,
)


MODEL_VERSION = (
    "statix-v7.2-fast-ensemble-1"
)


CLASS_NAMES = [
    "Strong Bearish",
    "Bearish",
    "Neutral",
    "Bullish",
    "Strong Bullish",
]


def _clean(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:

    x = df[
        columns
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    return (
        x
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
        .fillna(0.0)
        .astype(float)
    )


def _align_probs(
    model: Any,
    x: pd.DataFrame,
) -> np.ndarray:

    probabilities = (
        model
        .predict_proba(x)[0]
    )

    output = np.zeros(
        len(CLASS_NAMES),
        dtype=float,
    )

    for i, cls in enumerate(
        getattr(
            model,
            "classes_",
            [],
        )
    ):

        index = int(cls)

        if 0 <= index < len(
            CLASS_NAMES
        ):

            output[index] = (
                probabilities[i]
            )

    total = output.sum()

    if total:
        return output / total

    return np.ones(
        len(CLASS_NAMES)
    ) / len(CLASS_NAMES)


@st.cache_resource(
    ttl=21600,
    max_entries=150,
    show_spinner=False,
)
def _train_models(
    ticker: str,
    market_date: str,
    feature_columns: tuple[str, ...],
    training_df: pd.DataFrame,
):

    columns = list(
        feature_columns
    )

    x = _clean(
        training_df,
        columns,
    )

    y = pd.to_numeric(
        training_df["target"],
        errors="coerce",
    ).astype(int)

    future = pd.to_numeric(
        training_df[
            "future_return"
        ],
        errors="coerce",
    )

    valid = (
        future.notna()
        & y.notna()
    )

    x = x.loc[valid]
    y = y.loc[valid]
    future = future.loc[valid]

    if len(x) < 180:

        raise ValueError(
            f"Only {len(x)} usable rows "
            "are available; 180 are required."
        )

    if y.nunique() < 2:

        raise ValueError(
            "The training target contains "
            "fewer than two classes."
        )

    classifier_a = (
        HistGradientBoostingClassifier(
            max_iter=90,
            learning_rate=0.07,
            max_leaf_nodes=10,
            min_samples_leaf=12,
            l2_regularization=2.0,
            random_state=42,
        )
    )

    classifier_b = (
        LogisticRegression(
            solver="lbfgs",
            max_iter=800,
            C=0.6,
            random_state=42,
        )
    )

    regressor = (
        HistGradientBoostingRegressor(
            max_iter=90,
            learning_rate=0.07,
            max_leaf_nodes=10,
            min_samples_leaf=12,
            l2_regularization=2.0,
            random_state=42,
        )
    )

    classifier_a.fit(
        x,
        y,
    )

    classifier_b.fit(
        x,
        y,
    )

    regressor.fit(
        x,
        future,
    )

    return (
        classifier_a,
        classifier_b,
        regressor,
        len(x),
    )


def train_and_predict(
    training_df: pd.DataFrame,
    latest_df: pd.DataFrame,
    feature_columns: list[str],
    ticker: str = "UNKNOWN",
    market_date: str = "UNKNOWN",
    validate: bool = False,
) -> dict[str, Any]:

    if (
        training_df.empty
        or latest_df.empty
    ):

        raise ValueError(
            "Training or latest feature data is empty."
        )

    columns = tuple(
        feature_columns
    )

    x_latest = _clean(
        latest_df,
        list(columns),
    )

    (
        classifier_a,
        classifier_b,
        regressor,
        rows,
    ) = _train_models(
        ticker,
        market_date,
        columns,
        training_df,
    )

    p1 = _align_probs(
        classifier_a,
        x_latest,
    )

    p2 = _align_probs(
        classifier_b,
        x_latest,
    )

    probabilities = (
        p1 + p2
    ) / 2.0

    probabilities /= (
        probabilities.sum()
    )

    predicted_class = int(
        np.argmax(
            probabilities
        )
    )

    signal = CLASS_NAMES[
        predicted_class
    ]

    predictions = np.array(
        [
            np.argmax(p1),
            np.argmax(p2),
        ]
    )

    agreement = float(
        np.mean(
            predictions
            == predicted_class
        )
    )

    expected_return = float(
        regressor.predict(
            x_latest
        )[0]
    )

    expected_return = float(
        np.clip(
            expected_return,
            -1.0,
            1.0,
        )
    )

    probability_strength = max(
        0.0,
        (
            float(
                probabilities.max()
            )
            - 0.2
        )
        / 0.8,
    )

    confidence = float(
        np.clip(
            0.65
            * probability_strength
            + 0.35
            * agreement,
            0,
            1,
        )
    )

    result = {
        "signal": signal,
        "probability_up": float(
            probabilities[3]
            + probabilities[4]
        ),
        "expected_return": expected_return,
        "confidence": confidence,
        "class_probabilities": {
            CLASS_NAMES[i]: float(
                probabilities[i]
            )
            for i in range(5)
        },
        "model_agreement": agreement,
        "validation_accuracy": None,
        "baseline_accuracy": None,
        "validation_folds": 0,
        "training_rows": rows,
        "feature_count": len(columns),
        "rmse": None,
        "model_version": MODEL_VERSION,
    }

    if validate:

        result.update(
            _quick_validation(
                training_df,
                list(columns),
            )
        )

    return result


def _quick_validation(
    df: pd.DataFrame,
    columns: list[str],
) -> dict[str, Any]:

    if len(df) < 260:

        return {
            "validation_accuracy": None,
            "baseline_accuracy": None,
            "validation_folds": 0,
        }

    split = int(
        len(df) * 0.85
    )

    train = df.iloc[
        :split
    ]

    test = df.iloc[
        split:
    ]

    x_train = _clean(
        train,
        columns,
    )

    x_test = _clean(
        test,
        columns,
    )

    y_train = (
        pd.to_numeric(
            train["target"],
            errors="coerce",
        )
        .astype(int)
    )

    y_test = (
        pd.to_numeric(
            test["target"],
            errors="coerce",
        )
        .astype(int)
    )

    if y_train.nunique() < 2:

        return {
            "validation_accuracy": None,
            "baseline_accuracy": None,
            "validation_folds": 0,
        }

    model = (
        HistGradientBoostingClassifier(
            max_iter=70,
            learning_rate=0.08,
            max_leaf_nodes=10,
            min_samples_leaf=12,
            random_state=42,
        )
    )

    model.fit(
        x_train,
        y_train,
    )

    accuracy = float(
        (
            model.predict(x_test)
            == y_test
        ).mean()
    )

    baseline = float(
        y_train
        .value_counts(
            normalize=True
        )
        .max()
    )

    return {
        "validation_accuracy": accuracy,
        "baseline_accuracy": baseline,
        "validation_folds": 1,
    }