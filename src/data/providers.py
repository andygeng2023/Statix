from __future__ import annotations

from datetime import datetime, timezone
import os

import pandas as pd
import yfinance as yf


PROVIDERS = ["auto", "quantdash", "akshare", "yfinance"]


def _yahoo_symbol(ticker: str) -> str:
    symbol = ticker.upper().strip()
    if symbol.endswith((".SZ", ".SH", ".HK")):
        return symbol
    return symbol.replace(".", "-")


def _secret(name: str, default=None):
    try:
        import streamlit as st
        value = st.secrets.get(name, default)
        return value
    except Exception:
        return os.getenv(name, default)


def selected_provider() -> str:
    try:
        import streamlit as st
        if st.runtime.exists():
            value = st.session_state.get("provider_preference")
            if value:
                return str(value).lower()
    except Exception:
        pass

    return str(
        _secret("provider", os.getenv("STATIX_PROVIDER", "auto"))
    ).lower()


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    rename = {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
        "日期": "date",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "收盘": "close",
        "成交量": "volume",
        "trade_date": "date",
    }

    df = df.rename(columns=rename)

    if "date" in df.columns:
        df.index = pd.to_datetime(df["date"], errors="coerce")

    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="coerce")

    required = ["open", "high", "low", "close", "volume"]

    if not all(column in df.columns for column in required):
        return pd.DataFrame()

    df[required] = df[required].apply(
        pd.to_numeric,
        errors="coerce",
    )

    return (
        df[required]
        .dropna(subset=["close"])
        .sort_index()
    )


# ---------------------------------------------------------
# QuantDash
# ---------------------------------------------------------

def _quantdash():
    key = _secret("quantdash_api_key", "")

    if not key:
        return None

    try:
        from quantdash import QuantDash
        return QuantDash(api_key=key)
    except Exception:
        return None


def quantdash_history(ticker: str, limit: int = 1500) -> pd.DataFrame:
    client = _quantdash()

    if client is None:
        return pd.DataFrame()

    try:
        symbol = ticker.upper()

        # QuantDash uses market suffixes such as:
        # AAPL.US, 600519.SH, 000001.SZ
        if symbol.isalpha() and "." not in symbol:
            symbol = f"{symbol}.US"

        result = client.klines.get(
            symbol,
            period="1d",
            count=min(limit, 5000),
            adjust="forward",
            to_dataframe=True,
        )

        return _normalize(result)

    except Exception:
        return pd.DataFrame()


def quantdash_quote(ticker: str) -> dict:
    client = _quantdash()

    if client is None:
        return {}

    try:
        symbol = ticker.upper()

        if symbol.isalpha() and "." not in symbol:
            symbol = f"{symbol}.US"

        # QuantDash quote response is normalized defensively.
        result = client.quotes.get(
            symbols=[symbol],
            to_dataframe=True,
        )

        if result is None or result.empty:
            return {}

        row = result.iloc[0]

        def first(*names):
            for name in names:
                if name in result.columns and pd.notna(row[name]):
                    return row[name]
            return None

        price = first(
            "price",
            "last",
            "last_price",
            "close",
            "最新价",
        )

        if price is None:
            return {}

        change = first(
            "change_pct",
            "change_percent",
            "pct_change",
            "涨跌幅",
        )

        return {
            "ticker": ticker.upper(),
            "price": float(price),
            "change_pct": float(change) if change is not None else None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "provider": "quantdash",
        }

    except Exception:
        return {}


# ---------------------------------------------------------
# AKShare
# ---------------------------------------------------------

def akshare_history(ticker: str, limit: int = 1500) -> pd.DataFrame:
    try:
        import akshare as ak

        symbol = ticker.upper()

        if "." in symbol:
            symbol = symbol.split(".")[0]

        if symbol.isdigit():
            result = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                adjust="qfq",
            )
        else:
            result = ak.stock_us_daily(
                symbol=symbol,
                adjust="qfq",
            )

        return _normalize(result.tail(limit))

    except Exception:
        return pd.DataFrame()


def akshare_quote(ticker: str) -> dict:
    try:
        import akshare as ak

        symbol = ticker.upper().split(".")[0]

        if not symbol.isdigit():
            return {}

        data = ak.stock_zh_a_spot_em()

        row = data[
            data["代码"].astype(str) == symbol
        ]

        if row.empty:
            return {}

        item = row.iloc[0]

        return {
            "ticker": ticker.upper(),
            "price": float(item["最新价"]),
            "change_pct": float(item["涨跌幅"]),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "provider": "akshare",
        }

    except Exception:
        return {}


# ---------------------------------------------------------
# Yahoo
# ---------------------------------------------------------

def yahoo_history(
    ticker: str,
    period: str = "5y",
) -> pd.DataFrame:
    try:
        ticker = _yahoo_symbol(ticker)
        data = yf.download(
            ticker,
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
        )

        if data is None or data.empty:
            return pd.DataFrame()

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data.columns = [
            str(column).lower()
            for column in data.columns
        ]

        return _normalize(data)

    except Exception:
        return pd.DataFrame()


def yahoo_quote(ticker: str) -> dict:
    try:
        symbol = _yahoo_symbol(ticker)
        info = getattr(yf.Ticker(symbol), "fast_info", {}) or {}

        price = info.get("last_price") or info.get("regular_market_price")
        previous = info.get("previous_close")
        open_price = info.get("open") or info.get("regular_market_open")
        high = info.get("day_high") or info.get("regular_market_day_high")
        low = info.get("day_low") or info.get("regular_market_day_low")

        recent = pd.DataFrame()
        if price is None or open_price is None or high is None or low is None or previous is None:
            recent = yahoo_history(symbol, "5d")
            if not recent.empty:
                row = recent.iloc[-1]
                price = float(row["close"]) if price is None else price
                open_price = float(row["open"]) if open_price is None else open_price
                high = float(row["high"]) if high is None else high
                low = float(row["low"]) if low is None else low
                previous = float(recent["close"].iloc[-2]) if previous is None and len(recent) > 1 else previous

        if price is None:
            return {}

        change = None
        if previous not in (None, 0):
            change = (float(price) - float(previous)) / float(previous) * 100

        return {
            "ticker": symbol,
            "price": float(price),
            "change_pct": float(change) if change is not None else None,
            "open": float(open_price) if open_price is not None else None,
            "high": float(high) if high is not None else None,
            "low": float(low) if low is not None else None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "provider": "yfinance",
        }
    except Exception:
        return {}


# ---------------------------------------------------------
# Provider routing
# ---------------------------------------------------------

def _provider_order():
    provider = selected_provider()

    if provider != "auto":
        return [provider]

    return [
        "quantdash",
        "akshare",
        "yfinance",
    ]


def get_quote(ticker: str) -> dict:
    functions = {
        "quantdash": quantdash_quote,
        "akshare": akshare_quote,
        "yfinance": yahoo_quote,
    }

    merged = {}
    for provider in _provider_order():
        function = functions.get(provider)

        if function is None:
            continue

        result = function(ticker)

        if result:
            merged = {**merged, **{key: value for key, value in result.items() if value is not None}}
            if all(merged.get(field) is not None for field in ("price", "change_pct", "open", "high", "low")):
                break

    return merged


def get_history(
    ticker: str,
    period: str = "5y",
    limit: int = 1500,
) -> pd.DataFrame:

    functions = {
        "quantdash": quantdash_history,
        "akshare": akshare_history,
        "yfinance": lambda x, l: yahoo_history(x, period),
    }

    for provider in _provider_order():
        function = functions.get(provider)

        if function is None:
            continue

        result = function(ticker, limit)

        if result is not None and not result.empty:
            return result

    return pd.DataFrame()


def validate_symbol(ticker: str) -> bool:
    return bool(yahoo_quote(ticker))