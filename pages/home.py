import streamlit as st

from src.data.market import (
    get_quote,
    get_stock_data,
)

from src.storage.database import (
    get_recently_viewed,
    get_watchlist,
)

from src.ui.components import (
    mini_chart,
)


st.markdown(
    '<div class="statix-title">Statix</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="statix-subtitle">'
    "Predictive market intelligence"
    "</div>",
    unsafe_allow_html=True,
)


# -------------------------
# Quick actions
# -------------------------

c1, c2 = st.columns(2)

with c1:
    if st.button(
        "Search up a stock",
        use_container_width=True,
        type="primary",
    ):
        st.switch_page(
            "pages/search.py"
        )

with c2:
    if st.button(
        "Open Watchlist",
        use_container_width=True,
    ):
        st.switch_page(
            "pages/watchlist.py"
        )


st.divider()


# -------------------------
# Watchlist
# -------------------------

watchlist = get_watchlist()

st.subheader("Your Watchlist")

if not watchlist:

    st.info(
        "Your watchlist is empty."
    )

    st.page_link(
        "pages/search.py",
        label="Search stocks",
    )

else:

    for ticker in watchlist[:6]:

        with st.container(
            border=True
        ):

            try:
                quote = get_quote(
                    ticker
                )

                data = get_stock_data(
                    ticker,
                    period="3mo",
                )

                c1, c2 = st.columns(
                    [2, 4]
                )

                with c1:
                    st.subheader(
                        ticker
                    )

                    st.metric(
                        "Price",
                        (
                            f"${quote['price']:,.2f}"
                        ),
                        (
                            f"{quote['change_pct'] * 100:+.2f}%"
                        ),
                    )

                with c2:
                    st.plotly_chart(
                        mini_chart(data),
                        use_container_width=True,
                        config={
                            "displayModeBar": False
                        },
                    )

            except Exception as error:
                st.error(
                    f"{ticker}: {error}"
                )


# -------------------------
# Discover
# -------------------------

st.divider()

st.subheader("Discover")

st.caption(
    "Explore commonly followed market symbols."
)

discover = [
    (
        "AAPL",
        "Apple",
    ),
    (
        "MSFT",
        "Microsoft",
    ),
    (
        "NVDA",
        "NVIDIA",
    ),
    (
        "AMZN",
        "Amazon",
    ),
    (
        "GOOGL",
        "Alphabet",
    ),
    (
        "META",
        "Meta",
    ),
    (
        "TSLA",
        "Tesla",
    ),
    (
        "SPY",
        "S&P 500 ETF",
    ),
]


columns = st.columns(4)

for index, (
    ticker,
    name,
) in enumerate(discover):

    with columns[index % 4]:

        with st.container(
            border=True
        ):

            st.markdown(
                f"**{ticker}**"
            )

            st.caption(name)

            try:
                quote = get_quote(
                    ticker
                )

                st.metric(
                    "Price",
                    f"${quote['price']:,.2f}",
                    (
                        f"{quote['change_pct'] * 100:+.2f}%"
                    ),
                )

            except Exception:
                st.caption(
                    "Quote unavailable"
                )

            if st.button(
                "Analyze",
                key=f"discover_{ticker}",
                use_container_width=True,
            ):
                st.session_state[
                    "selected_ticker"
                ] = ticker

                st.switch_page(
                    "pages/prediction.py"
                )


# -------------------------
# Recently viewed
# -------------------------

recent = get_recently_viewed(
    limit=8
)

if recent:

    st.divider()

    st.subheader(
        "Recently Viewed"
    )

    columns = st.columns(4)

    for index, item in enumerate(
        recent
    ):

        with columns[index % 4]:

            with st.container(
                border=True
            ):

                st.markdown(
                    f"### {item['ticker']}"
                )

                st.caption(
                    item["direction"]
                    or "No prediction"
                )

                if (
                    item[
                        "probability_up"
                    ]
                    is not None
                ):
                    st.metric(
                        "Up Probability",
                        (
                            f"{item['probability_up'] * 100:.1f}%"
                        ),
                    )

                if st.button(
                    "Open",
                    key=(
                        f"recent_{item['ticker']}"
                    ),
                    use_container_width=True,
                ):
                    st.session_state[
                        "selected_ticker"
                    ] = item["ticker"]

                    st.switch_page(
                        "pages/prediction.py"
                    )