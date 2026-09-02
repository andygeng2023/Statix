import pandas as pd
import yfinance as yf
import streamlit as st


@st.cache_data(ttl=300)
def get_stock_data(
    ticker,
    period="2y",
):
    ticker = ticker.upper().strip()

    data = yf.download(
        ticker,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )

    if data.empty:
        raise ValueError(
            f"No data found for {ticker}"
        )

    if isinstance(
        data.columns,
        pd.MultiIndex,
    ):
        data.columns = (
            data.columns
            .get_level_values(0)
        )

    columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    data = data[columns].dropna()

    return data


@st.cache_data(ttl=300)
def get_quote(ticker):
    data = get_stock_data(
        ticker,
        period="5d",
    )

    latest = float(
        data["Close"].iloc[-1]
    )

    previous = float(
        data["Close"].iloc[-2]
    )

    change = latest - previous

    percentage = (
        change / previous
    )

    return {
        "price": latest,
        "change": change,
        "percentage": percentage,
    }