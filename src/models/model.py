from __future__ import annotations
import json
import numpy as np
import joblib
import streamlit as st
from src.config import MODEL_PATH, MODEL_META_PATH

CLASS_NAMES = ["Bearish", "Neutral", "Bullish"]
MODEL_VERSION = "statix-global-ensemble-v3"


class Ensemble:
    def __init__(self, logit, hgb, reg, features, mean, std, metrics):
        self.logit = logit
        self.hgb = hgb
        self.reg = reg
        self.feature_columns = features
        self.mean = np.asarray(mean)
        self.std = np.asarray(std)
        self.metrics = metrics

    def predict(self, X):
        # Training uses one vector per 64-day window. Inference must make
        # the same vector instead of accidentally predicting 64 separate rows.
        arr = np.asarray(X, dtype=float)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        vector = arr.mean(axis=0, keepdims=True)
        x = (vector - self.mean) / (self.std + 1e-8)

        p = (self.logit.predict_proba(x) + self.hgb.predict_proba(x)) / 2.0
        idx = int(np.argmax(p[0]))
        conf = float(p[0, idx])
        ret = float(self.reg.predict(x)[0])

        acc = float(self.metrics.get("validation_accuracy", 0.0))
        # This is a model-quality score, not a probability of future profit.
        rel = float(np.clip(0.60 * acc + 0.40 * conf, 0, 1))

        return {
            "direction": CLASS_NAMES[idx],
            "class_probabilities": {
                CLASS_NAMES[i]: float(p[0, i])
                for i in range(len(CLASS_NAMES))
            },
            "confidence": conf,
            "reliability": rel,
            "expected_return": ret,
        }


def train_global(X, y, r, features):
    mean = np.nanmean(X, axis=0)
    std = np.nanstd(X, axis=0)
    std[std < 1e-6] = 1.0
    xn = (X - mean) / (std + 1e-8)

    from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    clf = make_pipeline(
        StandardScaler(),
        LogisticRegression(
            max_iter=1200,
            class_weight="balanced",
            C=0.7,
            random_state=42,
        ),
    )
    clf.fit(xn, y)

    hgb = HistGradientBoostingClassifier(
        max_iter=260,
        learning_rate=0.045,
        max_leaf_nodes=31,
        l2_regularization=0.5,
        random_state=42,
    )
    hgb.fit(xn, y)

    reg = HistGradientBoostingRegressor(
        max_iter=260,
        learning_rate=0.045,
        max_leaf_nodes=31,
        l2_regularization=0.5,
        random_state=42,
    )
    reg.fit(xn, r)
    return clf, hgb, reg, mean, std


def save_model(logit, hgb, reg, features, mean, std, metrics):
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "logit": logit,
        "hgb": hgb,
        "reg": reg,
        "features": features,
        "mean": mean,
        "std": std,
        "metrics": metrics,
        "version": MODEL_VERSION,
    }, MODEL_PATH)
    MODEL_META_PATH.write_text(json.dumps({
        "model_version": MODEL_VERSION,
        "metrics": metrics,
        "features": features,
    }, indent=2))


@st.cache_resource(ttl=86400, show_spinner=False)
def load_model():
    if not MODEL_PATH.exists():
        return None
    try:
        p = joblib.load(MODEL_PATH)
        if p.get("version") != MODEL_VERSION:
            return None
        return Ensemble(
            p["logit"], p["hgb"], p["reg"], p["features"],
            np.asarray(p["mean"]), np.asarray(p["std"]), p["metrics"],
        )
    except Exception:
        return None
