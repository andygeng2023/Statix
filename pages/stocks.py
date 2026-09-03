import streamlit as st

st.title("Stocks")

st.write(
    "Search for a stock to open its full Statix page."
)

ticker = st.text_input(
    "Ticker",
    placeholder="AAPL",
).upper().strip()

if ticker:

    if st.button(
        "Open stock",
        type="primary",
    ):
        st.query_params["ticker"] = ticker
        st.switch_page(
            "pages/stock.py"
        )