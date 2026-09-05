from __future__ import annotations

import json

import joblib
import numpy as np
import streamlit as st
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.config import MODEL_PATH, MODEL_META_PATH

CLASS_NAMES_5 = ["Strong bearish", "Bearish", "Neutral", "Bullish", "Strong bullish"]
CLASS_NAMES_3 = ["Bearish", "Neutral", "Bullish"]
MODEL_VERSION = "statix-xgboost-lstm-v3"
SEQ = 64


def _class_names(classes) -> list[str]:
    classes = np.asarray(classes).reshape(-1)
    if len(classes) == 3:
        return CLASS_NAMES_3
    if len(classes) == 5:
        return CLASS_NAMES_5
    return [f"Class {x}" for x in classes]


def _prepare_prediction(X, mean, std):
    arr = np.asarray(X, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)

    # Training creates one sample by averaging the latest 64-day window.
    # The previous UI passed all 64 rows directly to predict_proba(), which
    # made the prediction shape/model semantics inconsistent.
    if arr.ndim != 2:
        raise ValueError("Prediction input must be a 1D or 2D numeric array.")

    if arr.shape[0] > 1:
        arr = arr[-SEQ:].mean(axis=0, keepdims=True)

    if arr.shape[1] != len(mean):
        raise ValueError(
            f"Feature count mismatch: model expects {len(mean)}, received {arr.shape[1]}."
        )

    arr = np.where(np.isfinite(arr), arr, np.nan)
    # Inference should not fail because one indicator produced a non-finite
    # value. Use the training statistic for that feature as the neutral fill.
    arr = np.where(np.isnan(arr), mean.reshape(1, -1), arr)
    return (arr - mean.reshape(1, -1)) / (std.reshape(1, -1) + 1e-8)


def _combined_probabilities(logit, hgb, x):
    p1 = np.asarray(logit.predict_proba(x), dtype=float)
    p2 = np.asarray(hgb.predict_proba(x), dtype=float)
    if p1.ndim == 1:
        p1 = p1.reshape(1, -1)
    if p2.ndim == 1:
        p2 = p2.reshape(1, -1)

    classes1 = np.asarray(getattr(logit, "classes_", np.arange(p1.shape[1])))
    classes2 = np.asarray(getattr(hgb, "classes_", np.arange(p2.shape[1])))

    if not np.array_equal(classes1, classes2):
        raise ValueError("Classifier class sets do not match.")

    return (p1 + p2) / 2.0, classes1


class Ensemble:
    def __init__(self, logit, hgb, reg, features, mean, std, metrics,
                 lstm_state=None, lstm_config=None):
        self.logit = logit
        self.hgb = hgb
        self.reg = reg
        self.feature_columns = features
        self.mean = np.asarray(mean, dtype=float)
        self.std = np.asarray(std, dtype=float)
        self.metrics = metrics or {}
        self.lstm = None
        if lstm_state and lstm_config:
            try:
                import torch
                from torch import nn

                class SequenceHead(nn.Module):
                    def __init__(self, input_size, hidden_size, classes):
                        super().__init__()
                        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
                        self.classifier = nn.Linear(hidden_size, classes)
                        self.regressor = nn.Linear(hidden_size, 1)

                    def forward(self, values):
                        output, _ = self.lstm(values)
                        state = output[:, -1, :]
                        return self.classifier(state), self.regressor(state).squeeze(-1)

                self.lstm = SequenceHead(**lstm_config)
                self.lstm.load_state_dict(lstm_state)
                self.lstm.eval()
            except Exception:
                self.lstm = None

    def predict(self, X):
        x = _prepare_prediction(X, self.mean, self.std)
        p, classes = _combined_probabilities(self.logit, self.hgb, x)
        sequence_return = None
        if self.lstm is not None:
            import torch
            sequence = np.asarray(X, dtype=float)
            if sequence.ndim == 2:
                sequence = sequence[-SEQ:]
            sequence = np.where(np.isfinite(sequence), sequence, self.mean)
            sequence = (sequence - self.mean) / (self.std + 1e-8)
            with torch.no_grad():
                logits, sequence_return = self.lstm(
                    torch.from_numpy(sequence.astype(np.float32)).unsqueeze(0)
                )
                sequence_probabilities = torch.softmax(logits, dim=1).numpy()
            p = 0.55 * p + 0.45 * sequence_probabilities

        row = p[0]
        idx = int(np.argmax(row))
        conf = float(row[idx])
        names = _class_names(classes)
        direction = names[idx]

        ret = float(self.reg.predict(x)[0])
        if sequence_return is not None:
            ret = 0.55 * ret + 0.45 * float(sequence_return.item())
        acc = float(self.metrics.get("validation_accuracy", 0.0))
        rel = float(np.clip(0.55 * conf + 0.45 * acc, 0.0, 1.0))

        return {
            "direction": direction,
            "class_probabilities": {
                names[i]: float(row[i]) for i in range(min(len(names), len(row)))
            },
            "confidence": conf,
            "reliability": rel,
            "expected_return": ret,
        }


def _clean_training_matrix(X):
    X = np.asarray(X, dtype=float)
    X = np.where(np.isfinite(X), X, np.nan)
    median = np.nanmedian(X, axis=0)
    median[~np.isfinite(median)] = 0.0
    rows, cols = np.where(np.isnan(X))
    if len(rows):
        X[rows, cols] = median[cols]
    return X


def train_global(X, y, r, features):
    raw_sequences = np.asarray(X, dtype=float)
    if raw_sequences.ndim == 3:
        X = raw_sequences.mean(axis=1)
    else:
        X = raw_sequences
    X = _clean_training_matrix(X)
    r = np.nan_to_num(np.asarray(r, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)

    mean = np.mean(X, axis=0)
    std = np.std(X, axis=0)
    mean[~np.isfinite(mean)] = 0.0
    std[~np.isfinite(std) | (std < 1e-6)] = 1.0

    xn = (X - mean) / (std + 1e-8)
    xn = np.nan_to_num(xn, nan=0.0, posinf=0.0, neginf=0.0)

    try:
        from xgboost import XGBClassifier, XGBRegressor
        clf = XGBClassifier(
            n_estimators=260, max_depth=5, learning_rate=0.04,
            subsample=0.85, colsample_bytree=0.85, objective="multi:softprob",
            eval_metric="mlogloss", random_state=42,
        )
        clf.fit(xn, y)
        hgb = clf
        reg = XGBRegressor(
            n_estimators=260, max_depth=5, learning_rate=0.04,
            subsample=0.85, colsample_bytree=0.85, objective="reg:squarederror",
            random_state=42,
        )
        reg.fit(xn, r)
    except ImportError:
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=800))
        clf.fit(xn, y)
        hgb = HistGradientBoostingClassifier(
            max_iter=180, learning_rate=0.055, max_leaf_nodes=31,
            l2_regularization=0.3, random_state=42,
        )
        hgb.fit(xn, y)
        reg = HistGradientBoostingRegressor(
            max_iter=180, learning_rate=0.055, max_leaf_nodes=31,
            l2_regularization=0.3, random_state=42,
        )
        reg.fit(xn, r)

    lstm_state = None
    lstm_config = None
    if raw_sequences.ndim == 3:
        try:
            import torch
            from torch import nn

            torch.manual_seed(42)
            class SequenceHead(nn.Module):
                def __init__(self, input_size, hidden_size, classes):
                    super().__init__()
                    self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
                    self.classifier = nn.Linear(hidden_size, classes)
                    self.regressor = nn.Linear(hidden_size, 1)

                def forward(self, values):
                    output, _ = self.lstm(values)
                    state = output[:, -1, :]
                    return self.classifier(state), self.regressor(state).squeeze(-1)

            classes = int(np.max(y)) + 1
            network = SequenceHead(raw_sequences.shape[2], 32, classes)
            optimizer = torch.optim.Adam(network.parameters(), lr=0.002)
            class_loss = nn.CrossEntropyLoss()
            values = np.where(np.isfinite(raw_sequences), raw_sequences, 0.0)
            values = (values - mean) / (std + 1e-8)
            inputs = torch.from_numpy(values.astype(np.float32))
            labels = torch.from_numpy(np.asarray(y, dtype=np.int64))
            returns = torch.from_numpy(np.asarray(r, dtype=np.float32))
            network.train()
            for _ in range(18):
                logits, estimate = network(inputs)
                loss = class_loss(logits, labels) + 0.35 * nn.functional.mse_loss(estimate, returns)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            lstm_state = network.state_dict()
            lstm_config = {"input_size": raw_sequences.shape[2], "hidden_size": 32, "classes": classes}
        except (ImportError, OSError) as exc:
            # A broken or unavailable optional torch wheel must not prevent
            # the tabular model from being trained and deployed.
            print(f"LSTM branch unavailable; continuing with XGBoost: {exc}")
    return clf, hgb, reg, mean, std, lstm_state, lstm_config


def save_model(logit, hgb, reg, features, mean, std, metrics,
               lstm_state=None, lstm_config=None):
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "logit": logit,
            "hgb": hgb,
            "reg": reg,
            "features": features,
            "mean": mean,
            "std": std,
            "metrics": metrics,
            "lstm_state": lstm_state,
            "lstm_config": lstm_config,
            "version": MODEL_VERSION,
        },
        MODEL_PATH,
    )
    MODEL_META_PATH.write_text(
        json.dumps(
            {"model_version": MODEL_VERSION, "metrics": metrics, "features": features},
            indent=2,
        )
    )


@st.cache_resource(ttl=86400, show_spinner=False)
def load_model():
    if not MODEL_PATH.exists():
        return None
    try:
        p = joblib.load(MODEL_PATH)
        if p.get("version") != MODEL_VERSION:
            return None
        return Ensemble(
            p["logit"],
            p["hgb"],
            p["reg"],
            p["features"],
            np.asarray(p["mean"], dtype=float),
            np.asarray(p["std"], dtype=float),
            p.get("metrics", {}),
            p.get("lstm_state"),
            p.get("lstm_config"),
        )
    except Exception:
        return None
