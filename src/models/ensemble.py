from dataclasses import dataclass

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
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from src.config import SETTINGS


MODEL_VERSION = SETTINGS.model_version


CLASS_NAMES = [
    "Strong Bearish",
    "Bearish",
    "Neutral",
    "Bullish",
    "Strong Bullish",
]


@dataclass
class GlobalModel:

    classifier_a: object

    classifier_b: object

    regressor: object

    validation_accuracy: float | None

    training_rows: int

    model_version: str


def _clean_training_data(
    training_df: pd.DataFrame,
    features: list[str],
):

    clean = training_df.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    clean = clean.dropna(
        subset=features
        + [
            "target",
            "future_return",
        ]
    )

    return clean


def _build_models():

    classifier_a = HistGradientBoostingClassifier(
        max_iter=120,
        learning_rate=0.055,
        max_leaf_nodes=15,
        l2_regularization=0.4,
        random_state=42,
    )

    classifier_b = Pipeline(
        [
            (
                "scale",
                StandardScaler(),
            ),
            (
                "model",
                LogisticRegression(
                    solver="lbfgs",
                    max_iter=1000,
                    C=0.5,
                    random_state=42,
                ),
            ),
        ]
    )

    regressor = HistGradientBoostingRegressor(
        max_iter=120,
        learning_rate=0.055,
        max_leaf_nodes=15,
        l2_regularization=0.4,
        loss="squared_error",
        random_state=42,
    )

    return (
        classifier_a,
        classifier_b,
        regressor,
    )


@st.cache_resource(
    ttl=21600,
    max_entries=100,
    show_spinner=False,
)
def train_global_model(
    training_df: pd.DataFrame,
    features: tuple[str, ...],
):

    features = list(features)

    clean = _clean_training_data(
        training_df,
        features,
    )

    if len(clean) < SETTINGS.minimum_training_rows:
        raise ValueError(
            "Not enough training data. "
            f"Need at least "
            f"{SETTINGS.minimum_training_rows} "
            "clean rows."
        )

    X = clean[features]

    y = clean["target"].astype(int)

    returns = (
        clean["future_return"]
        .astype(float)
    )

    unique_classes = sorted(
        y.unique().tolist()
    )

    if len(unique_classes) < 5:
        raise ValueError(
            "Training data does not contain "
            "all prediction classes."
        )

    split = int(len(X) * 0.8)

    if split < 250:
        raise ValueError(
            "Training history is too short."
        )

    X_train = X.iloc[:split]

    X_test = X.iloc[split:]

    y_train = y.iloc[:split]

    y_test = y.iloc[split:]

    returns_train = returns.iloc[:split]

    classifier_a, classifier_b, regressor = (
        _build_models()
    )

    classifier_a.fit(
        X_train,
        y_train,
    )

    classifier_b.fit(
        X_train,
        y_train,
    )

    regressor.fit(
        X_train,
        returns_train,
    )

    validation_accuracy = None

    if len(X_test) > 0:

        probabilities_a = (
            classifier_a
            .predict_proba(X_test)
        )

        probabilities_b = (
            classifier_b
            .predict_proba(X_test)
        )

        probabilities = (
            probabilities_a
            + probabilities_b
        ) / 2

        predictions = (
            classifier_a
            .classes_[
                np.argmax(
                    probabilities,
                    axis=1,
                )
            ]
        )

        validation_accuracy = float(
            accuracy_score(
                y_test,
                predictions,
            )
        )

    return GlobalModel(
        classifier_a=classifier_a,
        classifier_b=classifier_b,
        regressor=regressor,
        validation_accuracy=validation_accuracy,
        training_rows=len(clean),
        model_version=MODEL_VERSION,
    )


def predict_with_model(
    model: GlobalModel,
    latest_df: pd.DataFrame,
    features: list[str],
):

    X = latest_df[
        features
    ].replace(
        [np.inf, -np.inf],
        np.nan,
    )

    X = X.ffill().bfill()

    if X.isna().any().any():
        raise ValueError(
            "Latest market row contains "
            "missing model features."
        )

    p_a = (
        model.classifier_a
        .predict_proba(X)[0]
    )

    p_b = (
        model.classifier_b
        .predict_proba(X)[0]
    )

    probabilities = (
        p_a + p_b
    ) / 2

    predicted_class = int(
        np.argmax(probabilities)
    )

    probability = float(
        probabilities[predicted_class]
    )

    expected_return = float(
        model.regressor
        .predict(X)[0]
    )

    agreement = float(
        1
        - np.mean(
            np.abs(
                p_a - p_b
            )
        )
    )

    validation = (
        model.validation_accuracy
        if model.validation_accuracy
        is not None
        else 0.5
    )

    data_quality = 1.0

    reliability = float(
        np.clip(
            (
                probability * 0.45
                + agreement * 0.25
                + validation * 0.20
                + data_quality * 0.10
            ),
            0,
            1,
        )
    )

    class_probabilities = {
        name: float(probabilities[i])
        for i, name in enumerate(
            CLASS_NAMES
        )
    }

    return {
        "signal": CLASS_NAMES[
            predicted_class
        ],

        "class_id": predicted_class,

        "probability": probability,

        "class_probabilities": (
            class_probabilities
        ),

        "expected_return": expected_return,

        "reliability": reliability,

        "model_agreement": agreement,

        "validation_accuracy": (
            model.validation_accuracy
        ),

        "training_rows": (
            model.training_rows
        ),

        "model_version": (
            model.model_version
        ),
    }