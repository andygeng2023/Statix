import streamlit as st

from src.scanner.engine import scan


st.title("Scanner")

st.write(
    "Find stocks with strong model signals."
)

st.warning(
    "A large scan can take time because market data "
    "providers impose request and rate limits."
)

universe_text = st.text_area(
    "Universe",
    value=(
        "AAPL,MSFT,NVDA,AMZN,GOOGL,META,TSLA,"
        "AVGO,JPM,V,MA,UNH,COST,HD,PG,KO,PEP,NFLX,AMD"
    ),
    height=100,
)

limit = st.slider(
    "Number of results",
    min_value=5,
    max_value=50,
    value=20,
)

if st.button(
    "Run scan",
    type="primary",
):

    tickers = [
        x.strip().upper()
        for x in universe_text.split(",")
        if x.strip()
    ]

    with st.spinner(
        f"Scanning {len(tickers)} stocks..."
    ):

        results = scan(
            tickers,
            max_results=limit,
        )

    if not results:

        st.info(
            "No sufficiently reliable signals "
            "were found."
        )

    else:

        for result in results:

            with st.container(
                border=True
            ):

                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    st.subheader(
                        result["ticker"]
                    )

                with c2:
                    st.write(
                        result["signal"]
                    )

                with c3:
                    st.write(
                        f"5D: "
                        f"{result['return_5d']:.2%}"
                    )

                with c4:
                    st.write(
                        f"Reliability: "
                        f"{result['confidence']:.1%}"
                    )

                if st.button(
                    "Open",
                    key=(
                        "open_"
                        + result["ticker"]
                    ),
                ):

                    st.query_params[
                        "ticker"
                    ] = result["ticker"]

                    st.switch_page(
                        "pages/stock.py"
                    )