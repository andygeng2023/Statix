import streamlit as st

from src.data.market import get_quote
from src.storage.database import get_recent_views
from src.ui.components import prediction_card


st.title("Statix")

st.subheader("Market intelligence")

st.write(
    "Search a stock, inspect its market data, "
    "or view the model's current forecast."
)

ticker = st.text_input(
    "Search stock",
    placeholder="AAPL, MSFT, NVDA...",
).upper().strip()

if ticker:

    if st.button(
        f"Open {ticker}",
        type="primary",
    ):
        st.query_params["ticker"] = ticker
        st.switch_page(
            "pages/stock.py"
        )


st.divider()

recent = get_recent_views(
    limit=6
)

if recent:

    st.subheader(
        "Recently viewed"
    )

    cols = st.columns(
        min(6, len(recent))
    )

    for col, symbol in zip(
        cols,
        recent,
    ):

        with col:

            try:
                quote = get_quote(symbol)

                price = quote.get(
                    "price"
                )

                st.button(
                    f"{symbol}\n"
                    f"${price:,.2f}"
                    if price
                    else symbol,
                    key=f"recent_{symbol}",
                )

            except Exception:
                st.write(symbol)