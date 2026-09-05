from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import MAX_SCAN, ROOT, SCANNER_PREFILTER_LIMIT, SCANNER_RESULT_LIMIT, SEQUENCE_LENGTH
from src.data.market import get_history
from src.data.universe import load_universe
from src.data.providers import selected_provider
from src.models.features import create_features
from src.models.model import load_model
from src.models.scanner import prefilter

SECTOR_BY_SYMBOL = {
    "NVDA": "XLK", "MSFT": "XLK", "AAPL": "XLK", "AVGO": "XLK",
    "LLY": "XLV", "UNH": "XLV", "JNJ": "XLV", "JPM": "XLF",
    "V": "XLF", "MA": "XLF", "AMZN": "XLY", "WMT": "XLP",
    "XOM": "XLE", "CVX": "XLE", "CAT": "XLI", "GE": "XLI",
}


def universe(limit: int) -> list[str]:
    path = Path(ROOT) / "training" / "universe.txt"
    return load_universe(path, min(int(limit), MAX_SCAN))


def scan(limit: int, progress_callback=None) -> list[dict]:
    model = load_model()
    if model is None:
        raise RuntimeError(
            "The v4 model is not installed. Train it locally and commit "
            "artifacts/statix_model.joblib and artifacts/model_meta.json."
        )

    market = {
        ticker: get_history(ticker, "2y", 600)
        for ticker in ["SPY", "QQQ", "DIA", "IWM", "XLK", "XLV", "XLF", "XLY", "XLP", "XLE", "XLI"]
    }
    candidates = []
    symbols = universe(limit)
    total = len(symbols)
    for index, ticker in enumerate(symbols, start=1):
        if progress_callback:
            progress_callback(index, total, f"Loading {ticker}")
        try:
            history = get_history(ticker, "2y", 600)
            if len(history) < SEQUENCE_LENGTH:
                continue
            sector = market.get(SECTOR_BY_SYMBOL.get(ticker, "SPY"), market["SPY"])
            features, _ = create_features(history, market, sector, target=False)
            if len(features) < SEQUENCE_LENGTH:
                continue
            candidates.append({"ticker": ticker, "history": history, "features": features})
        except Exception:
            continue

    rows = []
    if progress_callback:
        progress_callback(0, max(1, min(len(candidates), SCANNER_PREFILTER_LIMIT)), "Ranking candidates")
    for candidate in prefilter(candidates, SCANNER_PREFILTER_LIMIT):
        features = candidate["features"]
        prediction = model.predict(
            features[model.feature_columns].tail(SEQUENCE_LENGTH).to_numpy()
        )
        history = candidate["history"]
        close = float(history["close"].iloc[-1])
        previous = float(history["close"].iloc[-2]) if len(history) > 1 else None
        change = (close - previous) / previous * 100 if previous not in (None, 0) else None
        momentum = float(candidate["prefilter_score"])
        risk = float(features["vol_20"].iloc[-1]) if "vol_20" in features else 0.0
        relative_strength = float(features["relative_ret_20"].iloc[-1])
        rank_score = (
            0.40 * prediction["confidence"]
            + 0.25 * np.clip(prediction["expected_return"] * 10, -1, 1)
            + 0.15 * prediction["reliability"]
            + 0.10 * np.clip(momentum, -1, 1)
            + 0.05 * np.clip(relative_strength * 10, -1, 1)
            + 0.05 * np.clip(-risk * 10, -1, 1)
        )
        rows.append({
            "ticker": candidate["ticker"],
            "signal": prediction["direction"],
            "confidence": prediction["confidence"],
            "reliability": prediction["reliability"],
            "expected_return": prediction["expected_return"],
            "price": close,
            "change_pct": change,
            "provider": selected_provider(),
            "rank_score": rank_score,
        })
        if progress_callback:
            progress_callback(
                len(rows),
                max(1, min(len(candidates), SCANNER_PREFILTER_LIMIT)),
                "Scoring candidates",
            )

    rows.sort(key=lambda row: row["rank_score"], reverse=True)
    return rows[:SCANNER_RESULT_LIMIT]