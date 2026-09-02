import streamlit as st

from src.data.market import (
    get_stock_data,
    get_quote,
)

from src.models.features import create_features

from src.models.ensemble import train_and_predict

from src.storage.database import get_watchlist

from src.ui.components import stock_card


st.markdown(
    '<div class="statix-title">Statix</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="statix-subtitle">'
    'Market intelligence and predictive analysis'
    '</div>',
    unsafe_allow_html=True,
)

watchlist = get_watchlist()

if not watchlist:
    st.info(
        "Your watchlist is empty. Search for a stock and add it."
    )

    st.page_link(
        "pages/search.py",
        label="Search stocks",
        icon="⌕",
    )

    st.stop()


st.subheader("Watchlist")

for ticker in watchlist[:6]:

    with st.container(border=True):

        with st.status(
            f"Analyzing {ticker}...",
            expanded=False,
        ) as status:

            try:
                data = get_stock_data(ticker)

                market = get_stock_data(
                    "SPY",
                    period="2y",
                )

                features, feature_columns = create_features(
                    data,
                    market,
                )

                prediction = train_and_predict(
                    features,
                    feature_columns,
                )

                quote = get_quote(ticker)

                status.update(
                    label=f"{ticker} analyzed",
                    state="complete",
                    expanded=False,
                )

                stock_card(
                    ticker,
                    quote,
                    prediction,
                    data.tail(90),
                )

            except Exception as e:

                status.update(
                    label=f"Could not analyze {ticker}",
                    state="error",
                )

                st.error(str(e))