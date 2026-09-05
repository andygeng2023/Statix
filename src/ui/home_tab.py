from __future__ import annotations

import streamlit as st

from src.data.market import history, quote
from src.data.search import security_name
from src.storage.database import get_settings, get_watchlist
from src.ui.components import card_row, t


settings = get_settings()

lang = st.session_state.get(
    "language_preference",
    settings.get("language", "en"),
)


st.markdown(f"# {t('home', lang)}")

st.caption(
    "Market overview, saved symbols and model signals."
)


watchlist = [
    str(x).upper()
    for x in get_watchlist()
]

watch_set = set(watchlist)

latest_rows = st.session_state.get(
    "latest_scan_rows",
    [],
)


def card_data(ticker: str, period: str = "6mo"):
    q = quote(ticker)
    df = history(ticker, period)

    return q, df


def make_items(
    symbols: list[str],
    period: str,
    exclude: set[str] | None = None,
):
    exclude = exclude or set()

    items = []

    for ticker in symbols:

        ticker = str(ticker).upper()

        if ticker in exclude:
            continue

        q, df = card_data(
            ticker,
            period,
        )

        items.append(
            {
                "ticker": ticker,
                "name": security_name(ticker),
                "price": q.get("price"),
                "change_pct": q.get("change_pct"),
                "df": df,
            }
        )

    return items


# ============================================================
# MARKET PULSE
# ============================================================

pulse_symbols = [
    "SPY",
    "QQQ",
    "DIA",
    "IWM",
]

pulse_symbols = [
    x
    for x in pulse_symbols
    if x not in watch_set
]


st.subheader(
    t("market_pulse", lang)
)

st.caption(
    "Major market benchmarks."
)

card_row(
    make_items(
        pulse_symbols,
        "3mo",
    ),
    key_prefix="home_pulse",
)


# ============================================================
# WATCHLIST
# ============================================================

if watchlist:

    st.subheader(
        t("watchlist", lang)
    )

    st.caption(
        "Your saved symbols."
    )

    card_row(
        make_items(
            watchlist[:12],
            "6mo",
        ),
        key_prefix="home_watchlist",
    )


# ============================================================
# DISCOVER
# ============================================================

st.subheader(
    t("discover", lang)
)

st.caption(
    "Recent model-ranked market signals."
)

discover_items = []

used = (
    set(pulse_symbols)
    | watch_set
)


for row in latest_rows[:16]:

    ticker = str(
        row.get("ticker", "")
    ).upper()

    if not ticker or ticker in used:
        continue

    q = quote(ticker)

    discover_items.append(
        {
            "ticker": ticker,
            "name": security_name(ticker),
            "price": q.get(
                "price",
                row.get("price"),
            ),
            "change_pct": q.get(
                "change_pct",
                row.get("change_pct"),
            ),
            "df": history(
                ticker,
                "6mo",
            ),
            "signal": row.get("signal"),
            "confidence": row.get("confidence"),
            "reliability": row.get("reliability"),
            "expected_return": row.get(
                "expected_return"
            ),
        }
    )

    used.add(ticker)


if discover_items:

    card_row(
        discover_items,
        key_prefix="home_discover",
    )

else:

    st.info(
        "No completed scan yet."
    )


# ============================================================
# POPULAR STOCKS
# ============================================================

featured_symbols = [
    "NVDA",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "AVGO",
    "TSLA",
    "AAPL",
    "AMD",
    "NFLX",
    "ORCL",
    "CRM",
]


st.subheader(
    t("top_stocks", lang)
)

st.caption(
    "Widely followed stocks."
)

featured_items = make_items(
    featured_symbols,
    "6mo",
    exclude=used,
)

card_row(
    featured_items,
    key_prefix="home_featured",
)