import streamlit as st
import yfinance as yf
import pandas as pd


DEFAULT_PERIOD = "5y"


@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(ticker: str, period: str = DEFAULT_PERIOD, interval: str = "1d"):
    ticker = ticker.upper().strip()

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

    if data is None or data.empty:
        return pd.DataFrame()

    # Handle yfinance MultiIndex columns
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    required = ["Open", "High", "Low", "Close", "Volume"]

    missing = [column for column in required if column not in data.columns]
    if missing:
        return pd.DataFrame()

    data = data[required].copy()
    data = data.dropna(subset=["Open", "High", "Low", "Close"])

    data.index = pd.to_datetime(data.index)
    data = data[~data.index.duplicated(keep="last")]
    data = data.sort_index()

    return data


@st.cache_data(ttl=30, show_spinner=False)
def get_quote(ticker: str):
    ticker = ticker.upper().strip()

    try:
        stock = yf.Ticker(ticker)
        info = stock.fast_info

        price = info.get("lastPrice")
        previous = info.get("previousClose")

        if price is not None:
            price = float(price)

        if previous is not None:
            previous = float(previous)

        change = None
        change_pct = None

        if price is not None and previous not in (None, 0):
            change = price - previous
            change_pct = (change / previous) * 100

        return {
            "ticker": ticker,
            "price": price,
            "previous_close": previous,
            "change": change,
            "change_pct": change_pct,
        }

    except Exception:
        pass

    # Historical fallback
    try:
        data = get_stock_data(ticker, period="5d")

        if len(data) >= 2:
            current = float(data["Close"].iloc[-1])
            previous = float(data["Close"].iloc[-2])

            change = current - previous
            change_pct = (change / previous) * 100 if previous else None

            return {
                "ticker": ticker,
                "price": current,
                "previous_close": previous,
                "change": change,
                "change_pct": change_pct,
            }

    except Exception:
        pass

    return {
        "ticker": ticker,
        "price": None,
        "previous_close": None,
        "change": None,
        "change_pct": None,
    }