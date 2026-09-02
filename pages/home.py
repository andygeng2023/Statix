import streamlit as st

from src.data.market import (
    get_quote,
    get_stock_data,
    format_volume,
)
from src.storage.database import (
    get_recently_viewed,
    get_watchlist,
)
from src.ui.components import (
    format_money,
    format_percent,
    format_probability,
    mini_chart,
)


st.markdown(
    """
    <div class="hero">
        <div class="hero-title">Statix</div>
        <div class="hero-subtitle">
            Market intelligence, predictions, and historical context in one dashboard.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# QUICK ACTIONS
# =========================================================

c1, c2, c3 = st.columns(3)

with c1:

    if st.button(
        "🔎 Search a stock",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/search.py"
        )


with c2:

    if st.button(
        "⭐ Open watchlist",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/watchlist.py"
        )


with c3:

    if st.button(
        "📊 Analyze SPY",
        use_container_width=True,
    ):

        st.session_state[
            "selected_ticker"
        ] = "SPY"

        st.switch_page(
            "pages/prediction.py"
        )


st.divider()


# =========================================================
# MARKET SNAPSHOT
# =========================================================

st.markdown(
    '<div class="section-title">Market snapshot</div>',
    unsafe_allow_html=True,
)

market_symbols = [
    "SPY",
    "QQQ",
    "DIA",
    "IWM",
]


cols = st.columns(4)

for col, ticker in zip(
    cols,
    market_symbols,
):

    quote = get_quote(ticker)

    with col:

        st.metric(
            ticker,
            format_money(
                quote.get("price")
            ),
            format_percent(
                quote.get(
                    "change_pct"
                )
            ),
        )


st.divider()


# =========================================================
# FEATURED STOCKS
# =========================================================

st.markdown(
    '<div class="section-title">Featured stocks</div>',
    unsafe_allow_html=True,
)

featured = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "AVGO",
]


for start in range(
    0,
    len(featured),
    4,
):

    row = featured[
        start:start + 4
    ]

    cols = st.columns(4)

    for col, ticker in zip(
        cols,
        row,
    ):

        with col:

            quote = get_quote(
                ticker
            )

            st.markdown(
                f"### {ticker}"
            )

            st.metric(
                "Price",
                format_money(
                    quote.get("price")
                ),
                format_percent(
                    quote.get(
                        "change_pct"
                    )
                ),
            )

            if st.button(
                "Analyze",
                key=f"home_analyze_{ticker}",
                use_container_width=True,
            ):

                st.session_state[
                    "selected_ticker"
                ] = ticker

                st.switch_page(
                    "pages/prediction.py"
                )


st.divider()


# =========================================================
# WATCHLIST
# =========================================================

st.markdown(
    '<div class="section-title">Watchlist</div>',
    unsafe_allow_html=True,
)

watchlist = get_watchlist()

if not watchlist:

    st.info(
        "Your watchlist is empty. Search for a stock to add one."
    )

else:

    for start in range(
        0,
        min(len(watchlist), 6),
        3,
    ):

        row = watchlist[
            start:start + 3
        ]

        cols = st.columns(3)

        for col, ticker in zip(
            cols,
            row,
        ):

            with col:

                quote = get_quote(
                    ticker
                )

                st.markdown(
                    f"**{ticker}**"
                )

                st.write(
                    format_money(
                        quote.get(
                            "price"
                        )
                    )
                )

                st.caption(
                    f"Today "
                    f"{format_percent(quote.get('change_pct'))}"
                )


st.divider()


# =========================================================
# RECENTLY VIEWED
# =========================================================

recent = get_recently_viewed(
    limit=8
)

st.markdown(
    '<div class="section-title">Recently analyzed</div>',
    unsafe_allow_html=True,
)

if not recent:

    st.caption(
        "Stocks you analyze will appear here."
    )

else:

    for start in range(
        0,
        len(recent),
        4,
    ):

        row = recent[
            start:start + 4
        ]

        cols = st.columns(4)

        for col, item in zip(
            cols,
            row,
        ):

            ticker = item[
                "ticker"
            ]

            with col:

                st.markdown(
                    f"### {ticker}"
                )

                st.caption(
                    item.get(
                        "direction",
                        "Neutral",
                    )
                )

                st.write(
                    "5D: "
                    + format_percent(
                        item.get(
                            "expected_return"
                        )
                    )
                )

                if st.button(
                    "Open",
                    key=f"recent_{ticker}",
                    use_container_width=True,
                ):

                    st.session_state[
                        "selected_ticker"
                    ] = ticker

                    st.switch_page(
                        "pages/prediction.py"
                    )


st.divider()


# =========================================================
# MARKET DATA STATUS
# =========================================================

st.markdown(
    '<div class="section-title">Data status</div>',
    unsafe_allow_html=True,
)

status_cols = st.columns(3)

with status_cols[0]:

    spy = get_stock_data(
        "SPY",
        period="5y",
    )

    st.metric(
        "SPY history",
        f"{len(spy):,} sessions",
    )


with status_cols[1]:

    st.metric(
        "Quote refresh",
        "~15 sec",
    )


with status_cols[2]:

    st.metric(
        "Model",
        "V6.1 Ensemble",
    )