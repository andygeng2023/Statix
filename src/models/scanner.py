from __future__ import annotations

import numpy as np
import pandas as pd


def kalman_level(values: pd.Series, process_noise: float = 1e-5,
                 measurement_noise: float = 1e-3) -> np.ndarray:
    """Return a fast one-dimensional Kalman estimate of a price series."""
    observations = np.asarray(values, dtype=float)
    if observations.size == 0:
        return observations

    estimate = float(observations[0])
    error = 1.0
    result = np.empty_like(observations)
    for index, observation in enumerate(observations):
        error += process_noise
        gain = error / (error + measurement_noise)
        estimate += gain * (float(observation) - estimate)
        error *= 1.0 - gain
        result[index] = estimate
    return result


def _graph_score(records: list[dict]) -> dict[str, float]:
    """Propagate recent returns across a correlation graph."""
    returns = {}
    for record in records:
        close = record["history"]["close"].astype(float)
        values = close.pct_change().dropna().tail(60).to_numpy()
        if len(values) >= 10:
            values = (values - values.mean()) / (values.std() + 1e-8)
        returns[record["ticker"]] = values

    scores = {}
    tickers = list(returns)
    for ticker in tickers:
        peers = []
        left = returns[ticker]
        for other in tickers:
            if other == ticker:
                continue
            right = returns[other]
            size = min(len(left), len(right))
            if size < 10:
                continue
            correlation = float(np.corrcoef(left[-size:], right[-size:])[0, 1])
            if np.isfinite(correlation) and correlation > 0.25:
                peers.append((correlation, float(right[-1])))
        peers.sort(reverse=True)
        neighbors = peers[:8]
        own_signal = float(left[-1]) if len(left) else 0.0
        neighbor_signal = (
            sum(weight * signal for weight, signal in neighbors)
            / sum(weight for weight, _ in neighbors)
            if neighbors else 0.0
        )
        scores[ticker] = 0.65 * own_signal + 0.35 * neighbor_signal
    return scores


def prefilter(records: list[dict], limit: int = 100) -> list[dict]:
    """Apply Kalman momentum, then graph propagation, before model scoring."""
    prepared = []
    for record in records:
        history = record["history"]
        close = history["close"].dropna().astype(float)
        if len(close) < 30:
            continue
        filtered = kalman_level(close)
        record = {**record, "kalman_return": float(filtered[-1] / filtered[-6] - 1)}
        prepared.append(record)

    graph_scores = _graph_score(prepared)
    for record in prepared:
        record["graph_score"] = graph_scores.get(record["ticker"], 0.0)
        record["prefilter_score"] = (
            0.55 * record["kalman_return"] + 0.45 * record["graph_score"]
        )
    return sorted(prepared, key=lambda row: row["prefilter_score"], reverse=True)[:limit]