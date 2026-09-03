from pathlib import Path

import numpy as np
import streamlit as st
import torch

from src.config import MODEL_PATH
from src.models.model import StatixModel
from src.models.features import (
    FEATURE_COLUMNS,
    make_sequence,
)


CLASS_NAMES = [
    "Strong Bearish",
    "Bearish",
    "Neutral",
    "Bullish",
    "Strong Bullish",
]


@st.cache_resource(
    ttl=21_600,
    max_entries=2,
    show_spinner=False,
)
def load_model():

    if not Path(MODEL_PATH).exists():
        return None

    checkpoint = torch.load(
        MODEL_PATH,
        map_location="cpu",
        weights_only=False,
    )

    model = StatixModel(
        input_dim=len(FEATURE_COLUMNS),
        d_model=checkpoint.get(
            "d_model",
            96,
        ),
    )

    model.load_state_dict(
        checkpoint["model"]
    )

    model.eval()

    return model


def predict(df):

    model = load_model()

    if model is None:
        return {
            "available": False,
            "reason": "Model artifact not installed.",
        }

    sequence = make_sequence(df)

    if sequence is None:
        return {
            "available": False,
            "reason": "Not enough clean market history.",
        }

    x = torch.tensor(
        sequence,
        dtype=torch.float32,
    ).unsqueeze(0)

    with torch.inference_mode():

        output = model(x)

        direction_probs = torch.softmax(
            output["direction"],
            dim=-1,
        )[0].numpy()

        predicted_returns = (
            output["returns"][0]
            .numpy()
        )

    index = int(np.argmax(direction_probs))

    probability = float(
        direction_probs[index]
    )

    confidence = probability

    # Penalize weak distributions.
    entropy = -np.sum(
        direction_probs *
        np.log(
            np.clip(
                direction_probs,
                1e-8,
                1,
            )
        )
    )

    max_entropy = np.log(5)

    entropy_score = 1 - (
        entropy / max_entropy
    )

    confidence = (
        0.7 * probability
        + 0.3 * entropy_score
    )

    return {
        "available": True,
        "signal": CLASS_NAMES[index],
        "class_index": index,
        "probability": probability,
        "confidence": float(confidence),
        "class_probabilities": {
            CLASS_NAMES[i]: float(
                direction_probs[i]
            )
            for i in range(5)
        },
        "return_1d": float(
            predicted_returns[0]
        ),
        "return_5d": float(
            predicted_returns[1]
        ),
        "return_20d": float(
            predicted_returns[2]
        ),
    }