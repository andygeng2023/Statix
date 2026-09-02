from __future__ import annotations

import time
from typing import Any

import pandas as pd
import yfinance as yf
import streamlit as st


DEFAULT_PERIOD = "5y"


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize yfinance columns into normal OHLCV columns."""

    if df is None or df.empty:
        return pd.DataFrame()

    result = df.copy()

    if isinstance(result.columns, pd.MultiIndex):
        result.columns = result.columns.get_level_values(0)

    result.columns = [str(col).strip().lower() for col in result.columns]

    rename_map = {
        "adj close": "adj_close",
    }

    result = result.rename(columns=rename_map)

    required = ["open", "high", "low", "close", "volume"]

    for column in required:
        if column not in result.columns:
            return pd.DataFrame()

    result = result[required].copy()

    for column in required:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    result = result.dropna(subset=["open", "high", "low", "close"])
    result = result.sort_index()
    result = result[~result.index.duplicated(keep="last")]

    return result


@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(
    ticker: str,
    period: str = DEFAULT_PERIOD,
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Historical market data.

    This is intentionally separate from quote data so refreshing
    a live quote never retrains a prediction model.
    """

    ticker = ticker.strip().upper()

    if not ticker:
        return pd.DataFrame()

    try:
        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
            threads=False,
        )
    except Exception:
        return pd.DataFrame()

    return _clean_columns(data)


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None

        value = float(value)

        if pd.isna(value):
            return None

        return value
    except Exception:
        return None


@st.cache_data(ttl=20, show_spinner=False)
def get_quote(ticker: str) -> dict[str, Any]:
    """
    Fast quote layer.

    Cached briefly so the UI can refresh without repeatedly
    downloading five years of historical data.
    """

    ticker = ticker.strip().upper()

    result: dict[str, Any] = {
        "ticker": ticker,
        "price": None,
        "previous_close": None,
        "change": None,
        "change_pct": None,
        "volume": None,
        "market_state": "Unknown",
        "updated_at": time.time(),
        "source": "Yahoo Finance",
    }

    if not ticker:
        return result

    try:
        instrument = yf.Ticker(ticker)
        info = instrument.fast_info

        price = _safe_float(info.get("last_price"))
        previous = _safe_float(info.get("previous_close"))

        if price is not None:
            result["price"] = price

        if previous is not None:
            result["previous_close"] = previous

        if price is not None and previous not in (None, 0):
            change = price - previous
            result["change"] = change
            result["change_pct"] = (change / previous) * 100

        volume = _safe_float(info.get("last_volume"))

        if volume is not None:
            result["volume"] = volume

    except Exception:
        pass

    # Reliable fallback from recent historical data.
    if result["price"] is None:
        try:
            recent = get_stock_data(
                ticker,
                period="5d",
                interval="1d",
            )

            if not recent.empty:
                close = recent["close"].dropna()

                if len(close) >= 1:
                    result["price"] = float(close.iloc[-1])

                if len(close) >= 2:
                    previous = float(close.iloc[-2])
                    price = float(close.iloc[-1])

                    result["previous_close"] = previous
                    result["change"] = price - previous

                    if previous != 0:
                        result["change_pct"] = (
                            (price - previous) / previous
                        ) * 100

                if "volume" in recent.columns:
                    volume = recent["volume"].dropna()

                    if not volume.empty:
                        result["volume"] = float(volume.iloc[-1])

        except Exception:
            pass

    result["updated_at"] = time.time()

    return result


def clear_market_cache() -> None:
    """Clear market-data caches."""

    get_stock_data.clear()
    get_quote.clear()