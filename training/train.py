from __future__ import annotations

from pathlib import Path
import os
import sys

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.metrics import accuracy_score, mean_squared_error

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.market import get_history
from src.models.features import create_features
from src.models.model import train_global, save_model, MODEL_VERSION

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "training" / "universe.txt"
SEQ = 64
DEFAULT_YEARS = "10y"


def yahoo_symbol(symbol: str) -> str:
    return symbol.upper().replace(".", "-")


def load_symbols():
    local = [
        x.strip().upper()
        for x in UNIVERSE.read_text().splitlines()
        if x.strip() and not x.startswith("#")
    ]

    # The repository file is a fallback/override. If it is still the tiny
    # starter universe, automatically expand it with the current S&P list.
    if len(local) < 100:
        try:
            remote = pd.read_csv(
                "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
            )
            local = remote["Symbol"].astype(str).str.upper().tolist()
        except Exception:
            pass

    # Keep a deterministic, de-duplicated universe.
    seen = set()
    symbols = []
    for s in local:
        if s not in seen:
            seen.add(s)
            symbols.append(s)

    max_symbols = int(os.getenv("STATIX_TRAIN_MAX_SYMBOLS", "500"))
    return symbols[:max_symbols]


def seqs(frame, cols):
    a = frame[cols].to_numpy(dtype=float)
    yy = frame["target"].to_numpy(dtype=int)
    rr = frame["future_return"].to_numpy(dtype=float)

    X, y, r = [], [], []
    for i in range(SEQ - 1, len(frame)):
        X.append(a[i - SEQ + 1:i + 1].mean(axis=0))
        y.append(yy[i])
        r.append(rr[i])
    return X, y, r


def download_batch(symbols, period=DEFAULT_YEARS):
    tickers = [yahoo_symbol(s) for s in symbols]
    data = yf.download(
        tickers=tickers,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=True,
        group_by="ticker",
    )
    return data


def extract_history(batch, yahoo_ticker):
    if batch is None or batch.empty:
        return pd.DataFrame()

    try:
        if isinstance(batch.columns, pd.MultiIndex):
            if yahoo_ticker not in batch.columns.get_level_values(0):
                return pd.DataFrame()
            d = batch[yahoo_ticker].copy()
        else:
            d = batch.copy()

        rename = {str(c): str(c).lower() for c in d.columns}
        d = d.rename(columns=rename)
        needed = ["open", "high", "low", "close", "volume"]
        if not all(c in d.columns for c in needed):
            return pd.DataFrame()
        return d[needed].dropna(subset=["close"]).sort_index()
    except Exception:
        return pd.DataFrame()


def main():
    symbols = load_symbols()
    years = os.getenv("STATIX_TRAIN_PERIOD", DEFAULT_YEARS)

    print(f"Universe: {len(symbols)} symbols")
    print(f"History: {years}")
    print("Downloading in batches from Yahoo Finance...")

    Xtr, ytr, rtr = [], [], []
    Xte, yte, rte = [], [], []
    feature_columns = None
    successful = 0

    # 50-at-a-time is fast enough without making one enormous request.
    for start in range(0, len(symbols), 50):
        group = symbols[start:start + 50]
        try:
            batch = download_batch(group, years)
        except Exception as exc:
            print(f"Batch {start + 1}-{start + len(group)} failed: {exc}")
            continue

        market = get_history("SPY", years, 3000)
        if market.empty:
            raise RuntimeError("Could not load SPY benchmark data.")

        for symbol in group:
            d = extract_history(batch, yahoo_symbol(symbol))
            if d.empty:
                continue

            try:
                frame, cols = create_features(d, market, target=True)
                if len(frame) < 220:
                    continue

                X, y, r = seqs(frame, cols)
                if len(X) < 120:
                    continue

                split = int(len(X) * 0.80)
                Xtr.extend(X[:split])
                ytr.extend(y[:split])
                rtr.extend(r[:split])
                Xte.extend(X[split:])
                yte.extend(y[split:])
                rte.extend(r[split:])
                feature_columns = cols
                successful += 1
            except Exception as exc:
                print(f"{symbol} failed: {exc}")

        print(
            f"Processed {min(start + 50, len(symbols))}/{len(symbols)} "
            f"symbols; usable={successful}"
        )

    if not Xtr or not Xte or feature_columns is None:
        raise RuntimeError("No usable training/validation data.")

    Xtr = np.asarray(Xtr, dtype=float)
    Xte = np.asarray(Xte, dtype=float)
    ytr = np.asarray(ytr, dtype=int)
    yte = np.asarray(yte, dtype=int)
    rtr = np.asarray(rtr, dtype=float)
    rte = np.asarray(rte, dtype=float)

    print()
    print(f"Training windows:   {len(Xtr)}")
    print(f"Validation windows: {len(Xte)}")
    print(f"Features:           {len(feature_columns)}")
    print(f"Usable symbols:     {successful}")
    print()

    clf, hgb, reg, mean, std = train_global(
        Xtr, ytr, rtr, feature_columns
    )

    Xte = np.nan_to_num(
    Xte,
    nan=0.0,
    posinf=0.0,
    neginf=0.0,
)

    Xte = np.clip(Xte, -20.0, 20.0)

    Xte_scaled = (Xte - mean) / (std + 1e-8)

    Xte_scaled = np.nan_to_num(
        Xte_scaled,
        nan=0.0,
        posinf=10.0,
        neginf=-10.0,
    )

    Xte_scaled = np.clip(Xte_scaled, -10.0, 10.0)
    probabilities = (
        clf.predict_proba(Xte_scaled)
        + hgb.predict_proba(Xte_scaled)
    ) / 2.0
    predictions = probabilities.argmax(axis=1)
    return_predictions = reg.predict(Xte_scaled)

    metrics = {
        "training_rows": int(len(Xtr)),
        "validation_rows": int(len(Xte)),
        "validation_accuracy": float(accuracy_score(yte, predictions)),
        "validation_rmse": float(
            np.sqrt(mean_squared_error(rte, return_predictions))
        ),
        "symbols": int(successful),
        "history_period": years,
        "sequence_length": SEQ,
        "classes": 3,
        "model_version": MODEL_VERSION,
    }

    save_model(
        clf, hgb, reg, feature_columns, mean, std, metrics
    )

    print()
    print("Training complete.")
    print(metrics)


if __name__ == "__main__":
    main()
