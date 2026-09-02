import time

import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st


DEFAULT_PERIOD = "5y"
QUOTE_TTL = 15
HISTORY_TTL = 300


@st.cache_data(ttl=HISTORY_TTL, show_spinner=False)
def get_stock_data(
    ticker: str,
    period: str = DEFAULT_PERIOD,
    interval: str = "1d",
) -> pd.DataFrame:

    ticker = ticker.upper().strip()

    try:
        df = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
            threads=False,
        )
    except Exception:
        return pd.DataFrame()

    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        try:
            df = df.xs(ticker, axis=1, level=-1)
        except Exception:
            df.columns = df.columns.get_level_values(0)

    required = ["Open", "High", "Low", "Close", "Volume"]

    for col in required:
        if col not in df.columns:
            return pd.DataFrame()

    df = df[required].copy()

    df.index = pd.to_datetime(df.index)

    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_localize(None)

    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]

    for col in required:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Open", "High", "Low", "Close"])

    return df


def _safe_number(value):
    try:
        value = float(value)

        if np.isnan(value) or np.isinf(value):
            return None

        return value
    except Exception:
        return None


@st.cache_data(ttl=QUOTE_TTL, show_spinner=False)
def get_quote(ticker: str) -> dict:

    ticker = ticker.upper().strip()

    result = {
        "ticker": ticker,
        "price": None,
        "previous": None,
        "change": None,
        "change_pct": None,
        "volume": None,
        "market_cap": None,
        "timestamp": time.time(),
    }

    try:
        obj = yf.Ticker(ticker)

        try:
            info = obj.fast_info

            price = _safe_number(
                info.get("last_price")
                or info.get("regularMarketPrice")
            )

            previous = _safe_number(
                info.get("previous_close")
                or info.get("regularMarketPreviousClose")
            )

            volume = _safe_number(info.get("last_volume"))
            market_cap = _safe_number(info.get("market_cap"))

            if price is not None:
                result["price"] = price

            if previous is not None:
                result["previous"] = previous

            if volume is not None:
                result["volume"] = volume

            if market_cap is not None:
                result["market_cap"] = market_cap

        except Exception:
            pass

        if result["price"] is None:
            fallback = get_stock_data(ticker, period="5d")

            if not fallback.empty:
                result["price"] = float(fallback["Close"].iloc[-1])

                if len(fallback) >= 2:
                    result["previous"] = float(
                        fallback["Close"].iloc[-2]
                    )

                result["volume"] = float(
                    fallback["Volume"].iloc[-1]
                )

    except Exception:
        return result

    if result["price"] is not None and result["previous"] is not None:
        result["change"] = (
            result["price"] - result["previous"]
        )

        if result["previous"] != 0:
            result["change_pct"] = (
                result["change"] / result["previous"]
            )

    return result


def get_latest_market_date(df: pd.DataFrame):
    if df is None or df.empty:
        return None

    return df.index[-1].date()


def format_volume(value):
    if value is None:
        return "—"

    value = float(value)

    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"

    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"

    if value >= 1_000:
        return f"{value / 1_000:.1f}K"

    return f"{value:,.0f}"