from __future__ import annotations

from pathlib import Path
import os
import sys

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.metrics import (
    accuracy_score, brier_score_loss, f1_score, mean_squared_error,
    precision_score, recall_score, roc_auc_score,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.market import get_history
from src.models.features import create_features
from src.models.model import train_global, save_model, MODEL_VERSION

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "training" / "universe.txt"
SEQ = 64
DEFAULT_YEARS = "10y"
SECTOR_ETFS = {
    "technology": {"XLK", "VGT", "SOXX", "AMD", "NVDA", "MSFT", "AAPL", "AVGO", "ORCL", "CRM", "ADBE"},
    "healthcare": {"XLV", "LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ISRG", "PFE"},
    "financials": {"XLF", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "BLK"},
    "consumer": {"XLY", "XLP", "AMZN", "WMT", "COST", "HD", "MCD", "NKE", "SBUX"},
    "energy": {"XLE", "XOM", "CVX", "COP", "SLB"},
    "industrials": {"XLI", "CAT", "GE", "HON", "UPS", "BA"},
}
SECTOR_TICKERS = {
    "technology": "XLK", "healthcare": "XLV", "financials": "XLF",
    "consumer": "XLY", "energy": "XLE", "industrials": "XLI",
}


def sector_etf(symbol):
    symbol = symbol.upper()
    for sector, members in SECTOR_ETFS.items():
        if symbol in members:
            return SECTOR_TICKERS[sector]
    return "SPY"


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


def seqs(frame, cols, max_windows=120, keep_sequences=False):
    a = frame[cols].to_numpy(dtype=np.float32)
    yy = frame["target"].to_numpy(dtype=int)
    rr = frame["future_return"].to_numpy(dtype=np.float32)

    end_indices = np.arange(SEQ - 1, len(frame))
    if len(end_indices) > max_windows:
        selected = np.linspace(0, len(end_indices) - 1, max_windows, dtype=int)
        end_indices = end_indices[selected]
    X = np.stack([a[i - SEQ + 1:i + 1] for i in end_indices]).astype(np.float32)
    if not keep_sequences:
        X = X.mean(axis=1).astype(np.float32)
    return X, yy[end_indices], rr[end_indices]


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
    Xtest, ytest, rtest = [], [], []
    feature_columns = None
    successful = 0
    keep_sequences = os.getenv("STATIX_ENABLE_LSTM", "0") == "1"
    market = {
        ticker: get_history(ticker, years, 3000)
        for ticker in ["SPY", "QQQ", "DIA", "IWM", "XLK", "XLV", "XLF", "XLY", "XLP", "XLE", "XLI"]
    }
    if market["SPY"].empty:
        raise RuntimeError("Could not load SPY benchmark data.")

    # 50-at-a-time is fast enough without making one enormous request.
    for start in range(0, len(symbols), 50):
        group = symbols[start:start + 50]
        try:
            batch = download_batch(group, years)
        except Exception as exc:
            print(f"Batch {start + 1}-{start + len(group)} failed: {exc}")
            continue

        for symbol in group:
            d = extract_history(batch, yahoo_symbol(symbol))
            if d.empty:
                continue

            try:
                sector_name = sector_etf(symbol)
                sector_frame = market.get(sector_name, market["SPY"])
                frame, cols = create_features(d, market, sector_frame, target=True)
                if len(frame) < 220:
                    continue

                train_end = int(len(frame) * 0.70)
                validation_end = int(len(frame) * 0.85)
                windows = int(os.getenv("STATIX_MAX_WINDOWS_PER_SYMBOL", "120"))
                train = seqs(
                    frame.iloc[:train_end], cols,
                    max_windows=windows,
                    keep_sequences=keep_sequences,
                )
                validation = seqs(
                    frame.iloc[max(0, train_end - SEQ + 1):validation_end],
                    cols, max_windows=max(40, windows // 3),
                    keep_sequences=keep_sequences,
                )
                test = seqs(
                    frame.iloc[max(0, validation_end - SEQ + 1):],
                    cols, max_windows=max(40, windows // 3),
                    keep_sequences=keep_sequences,
                )
                if min(len(train[0]), len(validation[0]), len(test[0])) == 0:
                    continue
                Xtr.extend(train[0]); ytr.extend(train[1]); rtr.extend(train[2])
                Xte.extend(validation[0]); yte.extend(validation[1]); rte.extend(validation[2])
                Xtest.extend(test[0]); ytest.extend(test[1]); rtest.extend(test[2])
                feature_columns = cols
                successful += 1
            except Exception as exc:
                print(f"{symbol} failed: {exc}")

        print(
            f"Processed {min(start + 50, len(symbols))}/{len(symbols)} "
            f"symbols; usable={successful}"
        )

    if not Xtr or not Xte or not Xtest or feature_columns is None:
        raise RuntimeError("No usable training/validation data.")

    Xtr = np.asarray(Xtr, dtype=np.float32)
    Xte = np.asarray(Xte, dtype=np.float32)
    Xtest = np.asarray(Xtest, dtype=np.float32)
    ytr = np.asarray(ytr, dtype=np.int64)
    yte = np.asarray(yte, dtype=np.int64)
    rtr = np.asarray(rtr, dtype=np.float32)
    rte = np.asarray(rte, dtype=np.float32)
    ytest = np.asarray(ytest, dtype=np.int64)
    rtest = np.asarray(rtest, dtype=np.float32)

    print()
    print(f"Training windows:   {len(Xtr)}")
    print(f"Validation windows: {len(Xte)}")
    print(f"Features:           {len(feature_columns)}")
    print(f"Usable symbols:     {successful}")
    print()

    clf, hgb, reg, mean, std, lstm_state, lstm_config = train_global(
        Xtr, ytr, rtr, feature_columns, Xte, yte
    )

    Xtest = np.nan_to_num(Xtest, nan=0.0, posinf=0.0, neginf=0.0)
    Xtest = Xtest.mean(axis=1) if Xtest.ndim == 3 else Xtest

    Xtest = np.clip(Xtest, -20.0, 20.0)

    Xtest_scaled = (Xtest - mean) / (std + 1e-8)

    Xtest_scaled = np.nan_to_num(
        Xtest_scaled,
        nan=0.0,
        posinf=10.0,
        neginf=-10.0,
    )

    Xtest_scaled = np.clip(Xtest_scaled, -10.0, 10.0)
    probabilities = (
        clf.predict_proba(Xtest_scaled)
        + hgb.predict_proba(Xtest_scaled)
    ) / 2.0
    predictions = probabilities.argmax(axis=1)
    return_predictions = reg.predict(Xtest_scaled)
    bullish_probability = probabilities[:, -1]
    test_slices = np.array_split(np.arange(len(ytest)), 3)
    slice_accuracy = [
        float(accuracy_score(ytest[indexes], predictions[indexes]))
        for indexes in test_slices if len(indexes)
    ]
    try:
        auc = float(roc_auc_score(ytest == 2, bullish_probability))
    except ValueError:
        auc = 0.5
    baseline = float(np.mean(ytest == 2))

    metrics = {
        "training_rows": int(len(Xtr)),
        "validation_rows": int(len(Xte)),
        "test_rows": int(len(Xtest)),
        "validation_accuracy": float(accuracy_score(ytest, predictions)),
        "test_precision": float(precision_score(ytest, predictions, average="macro", zero_division=0)),
        "test_recall": float(recall_score(ytest, predictions, average="macro", zero_division=0)),
        "test_f1": float(f1_score(ytest, predictions, average="macro", zero_division=0)),
        "test_roc_auc": auc,
        "test_brier": float(brier_score_loss(ytest == 2, bullish_probability)),
        "test_rmse": float(np.sqrt(mean_squared_error(rtest, return_predictions))),
        "test_average_predicted_return": float(np.mean(return_predictions)),
        "test_average_actual_return": float(np.mean(rtest)),
        "always_bullish_accuracy": baseline,
        "chronological_test_slice_accuracy": slice_accuracy,
        "validation_scheme": "70% train, 15% calibration, 15% chronological test",
        "symbols": int(successful),
        "history_period": years,
        "sequence_length": SEQ,
        "classes": 3,
        "model_version": MODEL_VERSION,
        "feature_version": "statix-point-in-time-features-v4",
        "feature_count": len(feature_columns),
        "training_start": str(market["SPY"].index.min().date()),
        "training_end": str(market["SPY"].index.max().date()),
    }

    save_model(
        clf, hgb, reg, feature_columns, mean, std, metrics,
        lstm_state, lstm_config
    )

    print()
    print("Training complete.")
    print(metrics)


if __name__ == "__main__":
    main()
