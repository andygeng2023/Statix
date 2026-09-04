from __future__ import annotations

import threading
import time
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.data.market import history, quote
from src.data.search import security_name
from src.storage.database import enqueue_scan, job_status, latest_scan
from src.storage.database import claim_job, finish_job
from scanner_worker import run as run_scan

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
app = FastAPI(title="Statix", version="2.0.0")
app.mount("/static", StaticFiles(directory=WEB), name="static")


def _worker_loop():
    while True:
        job_id = claim_job()
        if job_id is None:
            time.sleep(5)
            continue
        try:
            finish_job(job_id, run_scan(job_id))
        except Exception as exc:
            finish_job(job_id, [], exc)


@app.on_event("startup")
def start_worker():
    threading.Thread(target=_worker_loop, name="statix-scanner", daemon=True).start()

AREAS = {
    "Top stocks": ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "META", "AVGO", "TSLA"],
    "Technology": ["NVDA", "MSFT", "AAPL", "AVGO", "ORCL", "AMD", "CRM", "ADBE"],
    "Healthcare": ["LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ISRG", "PFE"],
    "Financials": ["JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "BLK"],
    "Consumer": ["AMZN", "WMT", "COST", "HD", "MCD", "NKE", "SBUX", "TJX"],
    "ETFs": ["SPY", "QQQ", "DIA", "IWM", "XLK", "XLF", "XLE", "ARKK"],
}


def _serialise(ticker: str, model: dict | None = None) -> dict:
    symbol = ticker.upper()
    q = quote(symbol)
    frame = history(symbol, "3mo")
    close = []
    if frame is not None and not frame.empty and "close" in frame:
        close = [float(value) for value in pd.to_numeric(frame["close"], errors="coerce").dropna().tail(60)]
    return {
        "ticker": symbol,
        "name": security_name(symbol),
        "price": q.get("price"),
        "change_pct": q.get("change_pct"),
        "close": close,
        **(model or {}),
    }


@app.get("/")
def index():
    return FileResponse(WEB / "index.html")


@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(WEB / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js")
def service_worker():
    return FileResponse(WEB / "sw.js", media_type="application/javascript")


@app.get("/api/areas")
def areas():
    return {"areas": list(AREAS)}


@app.get("/api/area/{area}")
def area(area: str):
    symbols = AREAS.get(area)
    if symbols is None:
        raise HTTPException(status_code=404, detail="Unknown area")
    return {"items": [_serialise(symbol) for symbol in symbols]}


@app.get("/api/overview")
def overview():
    return {
        "pulse": [_serialise(symbol) for symbol in ["SPY", "QQQ", "DIA", "IWM"]],
        "top": [_serialise(symbol) for symbol in AREAS["Top stocks"]],
    }


@app.get("/api/discover")
def discover():
    _, rows = latest_scan()
    items = []
    for row in rows:
        model = {key: row[key] for key in ("signal", "confidence", "reliability", "expected_return") if row.get(key) is not None}
        items.append(_serialise(row["ticker"], model))
    status = job_status()
    return {"items": items, "status": status.status if status else "idle"}


@app.post("/api/scan")
def scan(limit: int = 100):
    job_id = enqueue_scan(max(25, min(limit, 500)))
    if job_id is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"job_id": job_id}


@app.get("/api/stock/{ticker}")
def stock(ticker: str):
    item = _serialise(ticker)
    frame = history(ticker, "5y")
    if frame is not None and not frame.empty:
        try:
            from src.models.features import create_features
            from src.models.model import load_model

            model = load_model()
            features, _ = create_features(frame, history("SPY", "5y"), target=False)
            if model is not None and len(features) >= 64:
                item["prediction"] = model.predict(
                    features[model.feature_columns].tail(64).to_numpy()
                )
        except Exception:
            item["prediction"] = None
    return item
