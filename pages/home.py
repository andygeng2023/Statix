from __future__ import annotations

import streamlit as st

from src.data.market import get_quote, get_stock_data
from src.storage.database import (
    get_recently_viewed,
    get_watchlist,
)
from src.ui.components import (
    format_confidence,
    format_money,
    format_percent,
    format_probability,
    inject_css,
    mini_chart,
    page_header,
)


inject_css()


def select_stock(ticker: str) -> None:
    st.session_state["selected_ticker"] = ticker
    st.switch_page("pages/prediction.py")


page_header(
    "Statix",
    "Market data, model predictions, and historical context in one dashboard.",
)


# ---------------------------------------------------------
# Quick actions
# ---------------------------------------------------------

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button(
        "Search stocks",
        use_container_width=True,
    ):
        st.switch_page("pages/search.py")

with col2:
    if st.button(
        "Open watchlist",
        use_container_width=True,
    ):
        st.switch_page("pages/watchlist.py")


# ---------------------------------------------------------
# Market pulse
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">Market pulse</div>',
    unsafe_allow_html=True,
)

pulse_symbols = [
    ("SPY", "S&P 500"),
    ("QQQ", "Nasdaq 100"),
    ("DIA", "Dow Jones"),
]

pulse_cols = st.columns(3)

for column, (ticker, label) in zip(
    pulse_cols,
    pulse_symbols,
):
    with column:
        quote = get_quote(ticker)

        price = quote.get("price")
        change_pct = quote.get("change_pct")

        st.metric(
            label=f"{ticker} · {label}",
            value=format_money(price),
            delta=(
                format_percent(change_pct)
                if change_pct is not None
                else None
            ),
        )


# ---------------------------------------------------------
# Discover
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">Discover</div>',
    unsafe_allow_html=True,
)

discover = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "SPY",
]

for row_start in range(0, len(discover), 4):
    row = discover[row_start:row_start + 4]

    columns = st.columns(4)

    for column, ticker in zip(
        columns,
        row,
    ):
        with column:
            quote = get_quote(ticker)

            st.markdown(
                f"**{ticker}**"
            )

            st.caption(
                format_money(
                    quote.get("price")
                )
            )

            change = quote.get(
                "change_pct"
            )

            if change is not None:
                st.caption(
                    format_percent(change)
                )

            if st.button(
                "Analyze",
                key=f"home_{ticker}",
                use_container_width=True,
            ):
                select_stock(ticker)


# ---------------------------------------------------------
# Watchlist
# ---------------------------------------------------------

watchlist = get_watchlist()

if watchlist:
    st.markdown(
        '<div class="section-title">Your watchlist</div>',
        unsafe_allow_html=True,
    )

    watchlist = watchlist[:4]

    columns = st.columns(
        len(watchlist)
    )

    for column, ticker in zip(
        columns,
        watchlist,
    ):
        with column:
            quote = get_quote(ticker)

            st.markdown(
                f"**{ticker}**"
            )

            st.metric(
                "Price",
                format_money(
                    quote.get("price")
                ),
                (
                    format_percent(
                        quote.get("change_pct")
                    )
                    if quote.get("change_pct")
                    is not None
                    else None
                ),
            )

            if st.button(
                "Open",
                key=f"watch_{ticker}",
                use_container_width=True,
            ):
                select_stock(ticker)


# ---------------------------------------------------------
# Recently viewed
# ---------------------------------------------------------

recent = get_recently_viewed(
    limit=6
)

if recent:
    st.markdown(
        '<div class="section-title">Recently viewed</div>',
        unsafe_allow_html=True,
    )

    for row_start in range(
        0,
        len(recent),
        3,
    ):
        row = recent[
            row_start:row_start + 3
        ]

        columns = st.columns(3)

        for column, item in zip(
            columns,
            row,
        ):
            with column:
                ticker = item["ticker"]

                st.markdown(
                    f"**{ticker}**"
                )

                metrics = st.columns(2)

                with metrics[0]:
                    st.caption("Signal")
                    st.write(
                        item["direction"]
                        or "—"
                    )

                with metrics[1]:
                    st.caption("Up probability")
                    st.write(
                        format_probability(
                            item["probability_up"]
                        )
                    )

                st.caption(
                    f"Expected 5D return: "
                    f"{format_percent(item['expected_return'] * 100 if item['expected_return'] is not None else None)}"
                )

                if st.button(
                    "Open analysis",
                    key=f"recent_{ticker}_{row_start}",
                    use_container_width=True,
                ):
                    select_stock(ticker)


# ---------------------------------------------------------
# Empty-state help
# ---------------------------------------------------------

if not watchlist and not recent:
    st.divider()

    st.info(
        "Start by searching for a stock or selecting one "
        "from Discover. Your analyses will appear here "
        "after you view them."
    )