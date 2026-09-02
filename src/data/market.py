import yfinance as yf
import pandas as pd
import streamlit as st


@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(
    ticker: str,
    period: str = "2y",
    interval: str = "1d",
):
    ticker = ticker.upper().strip()

    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
    )

    if df.empty:
        raise ValueError(f"No market data found for {ticker}")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.columns = [str(c).title() for c in df.columns]

    required = ["Open", "High", "Low", "Close", "Volume"]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df[required].copy()
    df = df.dropna()

    return df


@st.cache_data(ttl=30, show_spinner=False)
def get_quote(ticker: str):
    ticker = ticker.upper().strip()

    stock = yf.Ticker(ticker)

    price = None
    previous_close = None

    try:
        fast = stock.fast_info

        price = fast.get("lastPrice")
        previous_close = fast.get("previousClose")

    except Exception:
        pass

    if price is None:
        data = get_stock_data(ticker, period="5d")

        if data.empty:
            raise ValueError(f"Could not retrieve quote for {ticker}")

        price = float(data["Close"].iloc[-1])

        if len(data) >= 2:
            previous_close = float(data["Close"].iloc[-2])

    if previous_close:
        change = price - previous_close
        change_pct = change / previous_close
    else:
        change = 0
        change_pct = 0

    return {
        "ticker": ticker,
        "price": float(price),
        "change": float(change),
        "change_pct": float(change_pct),
    }