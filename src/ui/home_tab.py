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
st.caption(t("overview", lang))


def card_data(
    ticker,
    period="6mo",
):
    q = quote(ticker)
    df = history(ticker, period)

    return q, df


watchlist = [
    str(x).upper()
    for x in get_watchlist()
]

watch_set = set(watchlist)

latest_rows = st.session_state.get(
    "latest_scan_rows",
    [],
)


# =========================================================
# SYMBOL GROUPS
# =========================================================

pulse_symbols = [
    "SPY",
    "QQQ",
    "DIA",
    "IWM",
]

pulse_symbols = [
    ticker
    for ticker in pulse_symbols
    if ticker not in watch_set
]


featured_symbols = [
    "NVDA",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "AVGO",
    "TSLA",
    "AAPL",
]


already_used = (
    set(pulse_symbols)
    | watch_set
)


featured_symbols = [
    ticker
    for ticker in featured_symbols
    if ticker not in already_used
]


def make_items(
    symbols,
    period,
):
    items = []

    for ticker in symbols:
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


# =========================================================
# MARKET PULSE
# =========================================================

st.subheader(
    t("market_pulse", lang)
)

st.caption(
    "Major market benchmarks"
)

card_row(
    make_items(
        pulse_symbols,
        "3mo",
    ),
    key_prefix="home_pulse",
)


# =========================================================
# WATCHLIST
# =========================================================

if watchlist:

    st.subheader(
        t("watch_suggestions", lang)
    )

    st.caption(
        "Your saved stocks"
    )

    card_row(
        make_items(
            watchlist[:8],
            "6mo",
        ),
        key_prefix="home_watchlist",
    )


# =========================================================
# DISCOVER
# =========================================================

st.subheader(
    t("discover", lang)
)

st.caption(
    "Recent scanner signals"
)

discover_items = []

used_discover = set(
    pulse_symbols
) | watch_set

for row in latest_rows[:16]:

    ticker = str(
        row.get("ticker", "")
    ).upper()

    if not ticker:
        continue

    if ticker in used_discover:
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
            "confidence": row.get(
                "confidence"
            ),
            "reliability": row.get(
                "reliability"
            ),
            "expected_return": row.get(
                "expected_return"
            ),
        }
    )

    used_discover.add(ticker)

if discover_items:
    card_row(
        discover_items,
        key_prefix="home_discover",
    )
else:
    st.info(
        t("no_scan", lang)
    )


# =========================================================
# POPULAR STOCKS
# =========================================================

st.subheader(
    t("top_stocks", lang)
)

st.caption(
    "Widely followed stocks"
)

featured_items = make_items(
    featured_symbols,
    "6mo",
)

# Avoid accidental duplication with
# scanner results displayed above.
discover_tickers = {
    item["ticker"]
    for item in discover_items
}

featured_items = [
    item
    for item in featured_items
    if item["ticker"]
    not in discover_tickers
]

if featured_items:
    card_row(
        featured_items,
        key_prefix="home_featured",
    )