from __future__ import annotations

import time
import pandas as pd

from src.config import MAX_SCAN, ROOT, SEQUENCE_LENGTH
from src.storage.database import claim_job, finish_job, job_limit
from src.data.providers import get_history
from src.data.providers import selected_provider
from src.models.features import create_features
from src.models.model import load_model


def universe(limit):
    path = ROOT / "training" / "universe.txt"
    rows = [
        x.strip().upper()
        for x in open(path, encoding="utf-8")
        if x.strip() and not x.startswith("#")
    ]
    if len(rows) < 100:
        try:
            remote = pd.read_csv(
                "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
            )
            rows = remote["Symbol"].astype(str).str.upper().tolist()
        except Exception:
            pass
    seen = set()
    rows = [x for x in rows if not (x in seen or seen.add(x))]
    return rows[:min(int(limit), MAX_SCAN)]


def run(job_id):
    model = load_model()
    if model is None:
        raise RuntimeError(
            "artifacts/statix_model.joblib is missing or outdated. "
            "Run python -m training.train and commit the artifact."
        )

    rows = []
    for ticker in universe(job_limit(job_id)):
        try:
            d = get_history(ticker, "2y", 600)
            if len(d) < SEQUENCE_LENGTH:
                continue

            f, _ = create_features(d, None, target=False)
            if len(f) < SEQUENCE_LENGTH:
                continue

            p = model.predict(
                f[model.feature_columns].tail(SEQUENCE_LENGTH).to_numpy()
            )

            close = float(d["close"].iloc[-1])
            previous = float(d["close"].iloc[-2]) if len(d) > 1 else None
            change = (
                (close - previous) / previous * 100
                if previous not in (None, 0) else None
            )

            rows.append({
                "ticker": ticker,
                "signal": p["direction"],
                "confidence": p["confidence"],
                "reliability": p["reliability"],
                "expected_return": p["expected_return"],
                "price": close,
                "change_pct": change,
                "provider": selected_provider(),
            })
        except Exception:
            continue

    rows.sort(
        key=lambda x: (
            x["expected_return"],
            x["reliability"],
            x["confidence"],
        ),
        reverse=True,
    )
    return rows[:25]


def main():
    poll = 5.0
    while True:
        jid = claim_job()
        if jid is None:
            time.sleep(poll)
            continue
        try:
            finish_job(jid, run(jid))
        except Exception as exc:
            finish_job(jid, [], exc)


if __name__ == "__main__":
    main()
