from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import MAX_SCAN, ROOT, SCANNER_PREFILTER_LIMIT, SCANNER_RESULT_LIMIT, SEQUENCE_LENGTH
from src.data.market import get_history
from src.data.providers import selected_provider
from src.models.features import create_features
from src.models.model import load_model
from src.models.scanner import prefilter


def universe(limit: int) -> list[str]:
    path = Path(ROOT) / "training" / "universe.txt"
    rows = [
        value.strip().upper()
        for value in path.read_text(encoding="utf-8").splitlines()
        if value.strip() and not value.startswith("#")
    ]
    if len(rows) < 100:
        try:
            remote = pd.read_csv(
                "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
            )
            rows = remote["Symbol"].astype(str).str.upper().tolist()
        except Exception:
            pass
    return list(dict.fromkeys(rows))[:min(int(limit), MAX_SCAN)]


def scan(limit: int) -> list[dict]:
    model = load_model()
    if model is None:
        raise RuntimeError(
            "The v3 model is not installed. Train it locally and commit "
            "artifacts/statix_model.joblib and artifacts/model_meta.json."
        )

    candidates = []
    for ticker in universe(limit):
        try:
            history = get_history(ticker, "2y", 600)
            if len(history) < SEQUENCE_LENGTH:
                continue
            features, _ = create_features(history, None, target=False)
            if len(features) < SEQUENCE_LENGTH:
                continue
            candidates.append({"ticker": ticker, "history": history, "features": features})
        except Exception:
            continue

    rows = []
    for candidate in prefilter(candidates, SCANNER_PREFILTER_LIMIT):
        features = candidate["features"]
        prediction = model.predict(
            features[model.feature_columns].tail(SEQUENCE_LENGTH).to_numpy()
        )
        history = candidate["history"]
        close = float(history["close"].iloc[-1])
        previous = float(history["close"].iloc[-2]) if len(history) > 1 else None
        change = (close - previous) / previous * 100 if previous not in (None, 0) else None
        rows.append({
            "ticker": candidate["ticker"],
            "signal": prediction["direction"],
            "confidence": prediction["confidence"],
            "reliability": prediction["reliability"],
            "expected_return": prediction["expected_return"],
            "price": close,
            "change_pct": change,
            "provider": selected_provider(),
        })

    rows.sort(
        key=lambda row: (row["expected_return"], row["reliability"], row["confidence"]),
        reverse=True,
    )
    return rows[:SCANNER_RESULT_LIMIT]