from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
from sklearn.metrics import accuracy_score, mean_squared_error

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.market import get_history
from src.models.features import create_features
from src.models.model import train_global, save_model, MODEL_VERSION


ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "training" / "universe.txt"

SEQ = 64


def seqs(f, cols):
    X = []
    y = []
    r = []

    a = f[cols].to_numpy(dtype=float)
    yy = f["target"].to_numpy(dtype=int)
    rr = f["future_return"].to_numpy(dtype=float)

    for i in range(SEQ - 1, len(f)):
        X.append(
            a[i - SEQ + 1:i + 1].mean(axis=0)
        )
        y.append(yy[i])
        r.append(rr[i])

    return X, y, r


def main():
    tickers = [
        x.strip().upper()
        for x in UNIVERSE.read_text().splitlines()
        if x.strip() and not x.startswith("#")
    ]

    market = get_history("SPY", "5y", 1500)

    if market.empty:
        raise RuntimeError("Could not load market benchmark data for SPY.")

    frames = []
    cols = None

    for i, ticker in enumerate(tickers, 1):
        try:
            data = get_history(ticker, "5y", 1500)

            if data.empty:
                print(f"[{i}/{len(tickers)}] {ticker} skipped: no data")
                continue

            frame, cols = create_features(
                data,
                market,
                target=True,
            )

            if len(frame) < 180:
                print(
                    f"[{i}/{len(tickers)}] {ticker} skipped: "
                    f"only {len(frame)} usable rows"
                )
                continue

            frame["_date"] = frame.index
            frames.append(frame)

            print(
                f"[{i}/{len(tickers)}] "
                f"{ticker} {len(frame)} rows"
            )

        except Exception as exc:
            print(
                f"[{i}/{len(tickers)}] "
                f"{ticker} failed: {exc}"
            )

    if not frames:
        raise RuntimeError("No usable training data.")

    # Collect all symbols first.
    Xtr = []
    ytr = []
    rtr = []

    Xte = []
    yte = []
    rte = []

    for frame in frames:
        X, y, r = seqs(frame, cols)

        if len(X) < 100:
            continue

        # Chronological split:
        # first 80% = training
        # final 20% = validation
        split = int(len(X) * 0.8)

        Xtr.extend(X[:split])
        ytr.extend(y[:split])
        rtr.extend(r[:split])

        Xte.extend(X[split:])
        yte.extend(y[split:])
        rte.extend(r[split:])

    if not Xtr or not Xte:
        raise RuntimeError(
            "Not enough training/validation data."
        )

    # Convert to NumPy exactly once.
    Xtr = np.asarray(Xtr, dtype=float)
    Xte = np.asarray(Xte, dtype=float)

    ytr = np.asarray(ytr, dtype=int)
    yte = np.asarray(yte, dtype=int)

    rtr = np.asarray(rtr, dtype=float)
    rte = np.asarray(rte, dtype=float)

    print()
    print(f"Training rows:   {len(Xtr)}")
    print(f"Validation rows: {len(Xte)}")
    print(f"Features:        {len(cols)}")
    print(f"Symbols:         {len(frames)}")
    print()

    # Train exactly once.
    logit, hgb, reg, mean, std = train_global(
        Xtr,
        ytr,
        rtr,
        cols,
    )

    # Normalize validation data using training statistics.
    Xte_scaled = (Xte - mean) / (std + 1e-8)

    # Classification ensemble.
    probabilities = (
        logit.predict_proba(Xte_scaled)
        + hgb.predict_proba(Xte_scaled)
    ) / 2.0

    predictions = probabilities.argmax(axis=1)

    # Regression prediction.
    return_predictions = reg.predict(Xte_scaled)

    metrics = {
        "training_rows": len(Xtr),
        "validation_rows": len(Xte),
        "validation_accuracy": float(
            accuracy_score(yte, predictions)
        ),
        "validation_rmse": float(
            np.sqrt(
                mean_squared_error(
                    rte,
                    return_predictions,
                )
            )
        ),
        "symbols": len(frames),
        "model_version": MODEL_VERSION,
    }

    save_model(
        logit,
        hgb,
        reg,
        cols,
        mean,
        std,
        metrics,
    )

    print()
    print("Training complete.")
    print(metrics)


if __name__ == "__main__":
    main()