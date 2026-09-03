from __future__ import annotations

import time
from typing import Any

import pandas as pd
import streamlit as st
import yfinance as yf


PROVIDER_NAME = (
    "Yahoo Finance via yfinance"
)


@st.cache_data(
    ttl=20,
    max_entries=500,
    show_spinner=False,
)
def get_quote(
    ticker: str,
) -> dict[str, Any]:

    ticker = ticker.strip().upper()

    if not ticker:
        return {}

    try:

        obj = yf.Ticker(
            ticker
        )

        info = obj.fast_info

        price = info.get(
            "last_price"
        )

        previous = info.get(
            "previous_close"
        )

        volume = (
            info.get("last_volume")
            or info.get(
                "regular_market_volume"
            )
        )

        # Fallback if fast_info does not provide a price.
        if price is None:

            history = obj.history(
                period="2d",
                interval="1m",
                auto_adjust=False,
            )

            if history.empty:

                history = obj.history(
                    period="5d",
                    interval="1d",
                    auto_adjust=False,
                )

            if not history.empty:

                price = float(
                    history["Close"].iloc[-1]
                )

                if volume is None:
                    volume = float(
                        history["Volume"].iloc[-1]
                    )

                if (
                    previous is None
                    and len(history) > 1
                ):
                    previous = float(
                        history["Close"].iloc[-2]
                    )

        change = None
        change_pct = None

        if (
            price is not None
            and previous not in (
                None,
                0,
            )
        ):

            change = float(
                price - previous
            )

            change_pct = float(
                change
                / previous
                * 100
            )

        return {
            "ticker": ticker,
            "price": (
                float(price)
                if price is not None
                else None
            ),
            "previous_close": (
                float(previous)
                if previous is not None
                else None
            ),
            "change": change,
            "change_pct": change_pct,
            "volume": (
                float(volume)
                if volume is not None
                else None
            ),
            "provider": PROVIDER_NAME,
            "updated_at": time.time(),
        }

    except Exception:

        return {
            "ticker": ticker,
            "provider": PROVIDER_NAME,
            "updated_at": time.time(),
        }


@st.cache_data(
    ttl=300,
    max_entries=250,
    show_spinner=False,
)
def get_stock_data(
    ticker: str,
    period: str = "5y",
    interval: str = "1d",
) -> pd.DataFrame:

    ticker = ticker.strip().upper()

    if not ticker:
        return pd.DataFrame()

    try:

        df = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )

    except Exception:

        return pd.DataFrame()

    if df.empty:
        return df

    if isinstance(
        df.columns,
        pd.MultiIndex,
    ):

        df.columns = [
            str(c[0]).lower()
            for c in df.columns
        ]

    else:

        df.columns = [
            str(c).lower()
            for c in df.columns
        ]

    df = df.rename(
        columns={
            "adj close": "adj_close",
        }
    )

    required = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    for column in required:

        if column not in df.columns:
            return pd.DataFrame()

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return (
        df
        .dropna(
            subset=["close"]
        )
        .sort_index()
    )


def clear_market_cache() -> None:
    get_quote.clear()
    get_stock_data.clear()