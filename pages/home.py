from __future__ import annotations

import streamlit as st

from src.data.market import (
    get_quote,
)
from src.storage.database import (
    get_recently_viewed,
    get_watchlist,
)
from src.ui.components import (
    format_money,
    format_percent,
    format_probability,
    inject_css,
    page_header,
)


inject_css()


def select_stock(
    ticker: str,
) -> None:

    st.session_state[
        "selected_ticker"
    ] = ticker.upper()

    st.switch_page(
        "pages/stock.py"
    )


page_header(
    "Statix",
    "Market data, historical context, and on-demand predictions.",
)


left, middle, right = st.columns(
    [1, 1, 2]
)


with left:

    if st.button(
        "Search stocks",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/search.py"
        )


with middle:

    if st.button(
        "Open watchlist",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/watchlist.py"
        )


st.markdown(
    '<div class="section-title">Market pulse</div>',
    unsafe_allow_html=True,
)


pulse = [
    (
        "SPY",
        "S&P 500",
    ),
    (
        "QQQ",
        "Nasdaq 100",
    ),
    (
        "DIA",
        "Dow Jones",
    ),
]


cols = st.columns(3)


for col, (
    ticker,
    label,
) in zip(
    cols,
    pulse,
):

    with col:

        quote = get_quote(
            ticker
        )

        st.metric(
            f"{ticker} · {label}",
            format_money(
                quote.get(
                    "price"
                )
            ),
            (
                format_percent(
                    quote.get(
                        "change_pct"
                    )
                )
                if quote.get(
                    "change_pct"
                )
                is not None
                else None
            ),
        )


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


for start in range(
    0,
    len(discover),
    4,
):

    row = discover[
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
                f"**{ticker}**"
            )

            st.write(
                format_money(
                    quote.get(
                        "price"
                    )
                )
            )

            change = quote.get(
                "change_pct"
            )

            if change is not None:

                st.caption(
                    format_percent(
                        change
                    )
                )

            if st.button(
                "View",
                key=f"discover_{ticker}",
                use_container_width=True,
            ):

                select_stock(
                    ticker
                )


watchlist = get_watchlist()


if watchlist:

    st.markdown(
        '<div class="section-title">Your watchlist</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(
        min(
            4,
            len(watchlist),
        )
    )

    for col, ticker in zip(
        cols,
        watchlist[:4],
    ):

        with col:

            quote = get_quote(
                ticker
            )

            st.markdown(
                f"**{ticker}**"
            )

            st.metric(
                "Price",
                format_money(
                    quote.get(
                        "price"
                    )
                ),
                (
                    format_percent(
                        quote.get(
                            "change_pct"
                        )
                    )
                    if quote.get(
                        "change_pct"
                    )
                    is not None
                    else None
                ),
            )

            if st.button(
                "Open",
                key=f"watch_{ticker}",
                use_container_width=True,
            ):

                select_stock(
                    ticker
                )


recent = get_recently_viewed(
    limit=6
)


if recent:

    st.markdown(
        '<div class="section-title">Recently viewed</div>',
        unsafe_allow_html=True,
    )

    for start in range(
        0,
        len(recent),
        3,
    ):

        row = recent[
            start:start + 3
        ]

        cols = st.columns(3)

        for col, item in zip(
            cols,
            row,
        ):

            with col:

                ticker = item[
                    "ticker"
                ]

                st.markdown(
                    f"**{ticker}**"
                )

                st.caption(
                    "Signal"
                )

                st.write(
                    item.get(
                        "direction"
                    )
                    or "—"
                )

                st.caption(
                    "Probability up"
                )

                st.write(
                    format_probability(
                        item.get(
                            "probability_up"
                        )
                    )
                )

                if st.button(
                    "Open",
                    key=f"recent_{ticker}_{start}",
                    use_container_width=True,
                ):

                    select_stock(
                        ticker
                    )


if not watchlist and not recent:

    st.info(
        "Search for a stock or select one from Discover."
    )