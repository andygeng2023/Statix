from __future__ import annotations

from datetime import datetime, timezone
import os
import pandas as pd
import yfinance as yf

PROVIDERS = ["auto", "quantdash", "akshare", "yfinance"]


def _secret(name: str, default=None):
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)


def selected_provider() -> str:
    try:
        import streamlit as st
        value = st.session_state.get("provider_preference")
        if value:
            return str(value).lower()
    except Exception:
        pass
    return str(_secret("provider", "auto")).lower()


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    rename = {
        "Open": "open", "High": "high", "Low": "low",
        "Close": "close", "Volume": "volume", "Adj Close": "close",
        "日期": "date", "开盘": "open", "最高": "high",
        "最低": "low", "收盘": "close", "成交量": "volume",
        "trade_date": "date",
    }
    df = df.rename(columns=rename)
    if "date" in df.columns:
        df.index = pd.to_datetime(df["date"], errors="coerce")
    else:
        df.index = pd.to_datetime(df.index, errors="coerce")
    required = ["open", "high", "low", "close", "volume"]
    if not all(c in df.columns for c in required):
        return pd.DataFrame()
    df[required] = df[required].apply(pd.to_numeric, errors="coerce")
    return df[required].dropna(subset=["close"]).sort_index()


def _quantdash():
    key = _secret("quantdash_api_key", "")
    if not key:
        return None
    try:
        from quantdash import QuantDash
        return QuantDash(api_key=str(key))
    except Exception:
        return None


def _qd_symbol(ticker: str) -> str:
    symbol = ticker.upper().strip()
    if "." not in symbol and symbol.isalpha():
        return f"{symbol}.US"
    return symbol


def quantdash_history(ticker: str, limit: int = 2500) -> pd.DataFrame:
    client = _quantdash()
    if client is None:
        return pd.DataFrame()
    try:
        result = client.klines.get(
            _qd_symbol(ticker),
            period="1d",
            count=min(int(limit), 5000),
            adjust="forward",
            to_dataframe=True,
        )
        return _normalize(result)
    except Exception:
        return pd.DataFrame()


def quantdash_quote(ticker: str) -> dict:
    # QuantDash's documented quote example is universe-based. To keep
    # the interactive UI fast, quote requests use Yahoo and QuantDash
    # remains available for historical data.
    return {}


def akshare_history(ticker: str, limit: int = 2500) -> pd.DataFrame:
    try:
        import akshare as ak
        symbol = ticker.upper().split(".")[0]
        if not symbol.isdigit():
            return pd.DataFrame()
        result = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
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
        row = data[data["代码"].astype(str) == symbol]
        if row.empty:
            return {}
        item = row.iloc[0]
        return {
            "ticker": ticker.upper(),
            "price": float(item["最新价"]),
            "change_pct": float(item["涨跌幅"]),
            "name": str(item.get("名称", ticker.upper())),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "provider": "akshare",
        }
    except Exception:
        return {}


def yahoo_history(ticker: str, period: str = "5y") -> pd.DataFrame:
    try:
        data = yf.download(
            ticker.upper(), period=period, interval="1d",
            auto_adjust=True, progress=False, threads=False,
        )
        if data is None or data.empty:
            return pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data.columns = [str(c).lower() for c in data.columns]
        return _normalize(data)
    except Exception:
        return pd.DataFrame()


def yahoo_quote(ticker: str) -> dict:
    try:
        symbol = ticker.upper()
        t = yf.Ticker(symbol)
        info = getattr(t, "fast_info", {}) or {}
        price = info.get("last_price") or info.get("regular_market_price")
        previous = info.get("previous_close")

        if price is None:
            data = yahoo_history(symbol, "5d")
            if data.empty:
                return {}
            price = float(data["close"].iloc[-1])
            previous = float(data["close"].iloc[-2]) if len(data) > 1 else None

        change = None
        if previous not in (None, 0):
            change = (float(price) - float(previous)) / float(previous) * 100

        name = symbol
        try:
            name = getattr(t, "info", {}).get("longName") or getattr(t, "info", {}).get("shortName") or symbol
        except Exception:
            pass

        return {
            "ticker": symbol,
            "price": float(price),
            "change_pct": change,
            "name": name,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "provider": "yfinance",
        }
    except Exception:
        return {}


def _provider_order():
    provider = selected_provider()
    if provider != "auto":
        return [provider]
    return ["quantdash", "akshare", "yfinance"]


def get_quote(ticker: str) -> dict:
    # Yahoo is the fast quote layer. Other configured providers are used
    # for markets they handle well; Yahoo remains the final fallback.
    functions = {
        "quantdash": quantdash_quote,
        "akshare": akshare_quote,
        "yfinance": yahoo_quote,
    }
    for provider in _provider_order():
        fn = functions.get(provider)
        if fn:
            result = fn(ticker)
            if result:
                return result
    return {}


def get_history(ticker: str, period: str = "5y", limit: int = 2500) -> pd.DataFrame:
    functions = {
        "quantdash": quantdash_history,
        "akshare": akshare_history,
        "yfinance": lambda x, l: yahoo_history(x, period),
    }
    for provider in _provider_order():
        fn = functions.get(provider)
        if fn:
            result = fn(ticker, limit)
            if result is not None and not result.empty:
                return result.tail(limit)
    return pd.DataFrame()


def validate_symbol(ticker: str) -> bool:
    return bool(yahoo_quote(ticker))
