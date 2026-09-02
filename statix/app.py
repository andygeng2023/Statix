import streamlit as st
import plotly.graph_objects as go

from market_data import (
    get_stock_data,
    get_quote,
)

from prediction import (
    create_features,
    train_model,
    predict,
)

from backtest import fast_backtest


# ==================================================
# CONFIG
# ==================================================

st.set_page_config(
    page_title="Stock Predictor",
    page_icon="📈",
    layout="wide",
)


# ==================================================
# SESSION STATE
# ==================================================

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

if "page" not in st.session_state:
    st.session_state.page = "Home"


# ==================================================
# HELPERS
# ==================================================

def add_to_watchlist(ticker):

    if ticker not in st.session_state.watchlist:
        st.session_state.watchlist.append(ticker)


def remove_from_watchlist(ticker):

    if ticker in st.session_state.watchlist:
        st.session_state.watchlist.remove(ticker)


def show_chart(ticker):

    data = get_stock_data(
        ticker,
        period="1y",
    )

    data = data.tail(180)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Close"],
            mode="lines",
            name=ticker,
        )
    )

    fig.update_layout(
        height=180,
        margin=dict(
            l=5,
            r=5,
            t=5,
            b=5,
        ),
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False
        },
    )


def stock_preview(ticker):

    try:

        quote = get_quote(ticker)

        change = (
            quote["percentage"] * 100
        )

        st.markdown(
            f"### {ticker}"
        )

        st.metric(
            "Price",
            f"${quote['price']:.2f}",
            f"{change:.2f}%",
        )

        show_chart(ticker)

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "Open",
                key=f"open_{ticker}",
            ):
                st.session_state.selected = ticker
                st.session_state.page = "Search"
                st.rerun()

        with col2:

            if ticker in st.session_state.watchlist:

                if st.button(
                    "Remove",
                    key=f"remove_{ticker}",
                ):
                    remove_from_watchlist(ticker)
                    st.rerun()

            else:

                if st.button(
                    "Add",
                    key=f"add_{ticker}",
                ):
                    add_to_watchlist(ticker)
                    st.rerun()

    except Exception:

        st.error(
            f"Unable to load {ticker}"
        )


# ==================================================
# NAVIGATION
# ==================================================

st.title("Stock Predictor")

nav1, nav2, nav3 = st.columns(3)

with nav1:

    if st.button(
        "Home",
        use_container_width=True,
    ):
        st.session_state.page = "Home"
        st.rerun()

with nav2:

    if st.button(
        "Watchlist",
        use_container_width=True,
    ):
        st.session_state.page = "Watchlist"
        st.rerun()

with nav3:

    if st.button(
        "Search",
        use_container_width=True,
    ):
        st.session_state.page = "Search"
        st.rerun()


st.divider()


# ==================================================
# HOME
# ==================================================

if st.session_state.page == "Home":

    st.header("Market Dashboard")

    st.write(
        "Search a stock or select one from your watchlist."
    )

    search = st.text_input(
        "Quick search",
        placeholder="Enter ticker, e.g. AAPL",
    )

    if search:

        ticker = search.upper().strip()

        try:

            quote = get_quote(ticker)

            st.subheader(ticker)

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Price",
                f"${quote['price']:.2f}",
            )

            col2.metric(
                "Daily change",
                f"{quote['percentage']:.2%}",
            )

            col3.metric(
                "Change",
                f"${quote['change']:.2f}",
            )

            if st.button(
                "Analyze prediction",
                type="primary",
            ):
                st.session_state.selected = ticker
                st.session_state.page = "Search"
                st.rerun()

        except Exception:

            st.error(
                "Stock not found. Try another ticker."
            )


    st.subheader("Watchlist")

    if not st.session_state.watchlist:

        st.info(
            "Your watchlist is empty."
        )

    else:

        columns = st.columns(3)

        for i, ticker in enumerate(
            st.session_state.watchlist
        ):

            with columns[i % 3]:

                stock_preview(ticker)


# ==================================================
# WATCHLIST
# ==================================================

elif st.session_state.page == "Watchlist":

    st.header("My Watchlist")

    if not st.session_state.watchlist:

        st.info(
            "Add stocks from Search or Home."
        )

    else:

        columns = st.columns(3)

        for i, ticker in enumerate(
            st.session_state.watchlist
        ):

            with columns[i % 3]:

                stock_preview(ticker)


# ==================================================
# SEARCH / PREDICTION
# ==================================================

elif st.session_state.page == "Search":

    st.header("Search")

    default = st.session_state.get(
        "selected",
        "",
    )

    ticker = st.text_input(
        "Ticker",
        value=default,
        placeholder="AAPL",
    ).upper().strip()


    if ticker:

        try:

            data = get_stock_data(
                ticker,
                period="2y",
            )

            st.subheader(ticker)

            quote = get_quote(ticker)

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Current price",
                    f"${quote['price']:.2f}",
                )

            with col2:

                st.metric(
                    "Daily change",
                    f"{quote['percentage']:.2%}",
                )


            # --------------------------------------
            # Watchlist
            # --------------------------------------

            if ticker in st.session_state.watchlist:

                if st.button(
                    "Remove from watchlist"
                ):
                    remove_from_watchlist(ticker)
                    st.rerun()

            else:

                if st.button(
                    "Add to watchlist"
                ):
                    add_to_watchlist(ticker)
                    st.rerun()


            # --------------------------------------
            # Chart
            # --------------------------------------

            st.subheader("Price")

            fig = go.Figure()

            fig.add_trace(
                go.Candlestick(
                    x=data.index,
                    open=data["Open"],
                    high=data["High"],
                    low=data["Low"],
                    close=data["Close"],
                    name=ticker,
                )
            )

            fig.update_layout(
                height=500,
                xaxis_rangeslider_visible=False,
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )


            # --------------------------------------
            # Prediction
            # --------------------------------------

            st.subheader(
                "Prediction"
            )

            horizon = st.selectbox(
                "Prediction horizon",
                [1, 3, 5, 10, 20],
                index=2,
            )

            features = create_features(
                data,
                horizon=horizon,
            )

            if len(features) < 250:

                st.warning(
                    "Not enough data for this model."
                )

            else:

                with st.spinner(
                    "Calculating prediction..."
                ):

                    model, accuracy = (
                        train_model(features)
                    )

                    result = predict(
                        model,
                        features,
                    )


                p1, p2, p3 = st.columns(3)

                p1.metric(
                    "Direction",
                    result["direction"],
                )

                p2.metric(
                    "Probability UP",
                    f"{result['probability_up']:.1%}",
                )

                p3.metric(
                    "Model accuracy",
                    f"{accuracy:.1%}",
                )


                if result["probability_up"] >= 0.60:

                    st.success(
                        "Model currently favors an upward move."
                    )

                elif result["probability_up"] <= 0.40:

                    st.error(
                        "Model currently favors a downward move."
                    )

                else:

                    st.info(
                        "Model signal is relatively uncertain."
                    )


                # ----------------------------------
                # Fast backtest
                # ----------------------------------

                with st.expander(
                    "Model validation"
                ):

                    backtest = fast_backtest(
                        features
                    )

                    st.write(
                        "Chronological validation accuracy:"
                    )

                    st.write(
                        f"{backtest['accuracy']:.1%}"
                    )


        except Exception as error:

            st.error(
                f"Unable to analyze {ticker}: {error}"
            )