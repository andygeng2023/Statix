import streamlit as st
import plotly.graph_objects as go

from market_data import get_stock_data
from prediction import create_features, train_model, predict_next
from backtest import walk_forward_backtest


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Stock Prediction Lab",
    page_icon="📈",
    layout="wide",
)


# --------------------------------------------------
# Title
# --------------------------------------------------

st.title("Stock Prediction Lab")

st.write(
    "Experimental machine-learning stock prediction dashboard."
)

st.warning(
    "Predictions are experimental estimates and are not financial advice."
)


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

st.sidebar.header("Settings")

ticker = st.sidebar.text_input(
    "Stock ticker",
    value="AAPL"
).upper().strip()

period = st.sidebar.selectbox(
    "Historical data",
    ["1y", "2y", "5y", "10y"],
    index=2,
)

horizon = st.sidebar.selectbox(
    "Prediction horizon",
    [1, 3, 5, 10, 20],
    index=2,
)

run_backtest = st.sidebar.checkbox(
    "Run backtest",
    value=True,
)

analyze = st.sidebar.button(
    "Analyze stock",
    type="primary",
)


# --------------------------------------------------
# Main application
# --------------------------------------------------

if analyze:

    try:

        # ------------------------------------------
        # Download data
        # ------------------------------------------

        with st.spinner("Downloading market data..."):

            data = get_stock_data(
                ticker,
                period=period,
            )


        # ------------------------------------------
        # Create prediction features
        # ------------------------------------------

        with st.spinner("Creating features..."):

            df = create_features(
                data,
                horizon=horizon,
            )


        if len(df) < 300:

            st.error(
                "There is not enough historical data "
                "for this analysis."
            )

            st.stop()


        # ------------------------------------------
        # Train model
        # ------------------------------------------

        with st.spinner("Training prediction model..."):

            model, accuracy = train_model(df)


        # ------------------------------------------
        # Generate prediction
        # ------------------------------------------

        prediction = predict_next(
            df,
            model,
        )


        # ------------------------------------------
        # Current price
        # ------------------------------------------

        current_price = float(
            data["Close"].iloc[-1]
        )


        # ------------------------------------------
        # Display main metrics
        # ------------------------------------------

        st.header(ticker)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Current price",
            f"${current_price:.2f}",
        )

        col2.metric(
            "Prediction",
            prediction["direction"],
        )

        col3.metric(
            "Probability UP",
            f"{prediction['probability_up']:.1%}",
        )

        col4.metric(
            "Test accuracy",
            f"{accuracy:.1%}",
        )


        # ------------------------------------------
        # Price chart
        # ------------------------------------------

        st.subheader("Price history")

        chart_data = data.tail(365)

        fig = go.Figure()

        fig.add_trace(
            go.Candlestick(
                x=chart_data.index,
                open=chart_data["Open"],
                high=chart_data["High"],
                low=chart_data["Low"],
                close=chart_data["Close"],
                name=ticker,
            )
        )

        fig.update_layout(
            height=550,
            xaxis_rangeslider_visible=False,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


        # ------------------------------------------
        # Prediction details
        # ------------------------------------------

        st.subheader(
            f"{horizon}-Trading-Day Prediction"
        )

        p1, p2 = st.columns(2)

        with p1:

            st.metric(
                "Direction",
                prediction["direction"],
            )

            st.write(
                f"Probability of UP: "
                f"**{prediction['probability_up']:.2%}**"
            )

            st.write(
                f"Probability of DOWN: "
                f"**{prediction['probability_down']:.2%}**"
            )


        with p2:

            st.write(
                "Model: **Random Forest Classifier**"
            )

            st.write(
                "Prediction target: "
                f"price direction after {horizon} "
                "trading days."
            )


        # ------------------------------------------
        # Backtest
        # ------------------------------------------

        if run_backtest:

            st.subheader(
                "Walk-Forward Backtest"
            )

            with st.spinner(
                "Running historical backtest..."
            ):

                results, backtest_accuracy = (
                    walk_forward_backtest(
                        df,
                        horizon=horizon,
                    )
                )


            b1, b2, b3 = st.columns(3)

            b1.metric(
                "Directional accuracy",
                f"{backtest_accuracy:.1%}",
            )

            b2.metric(
                "Predictions tested",
                len(results),
            )

            b3.metric(
                "Average probability UP",
                f"{results['probability_up'].mean():.1%}",
            )


            # --------------------------------------
            # Backtest chart
            # --------------------------------------

            st.subheader(
                "Predictions vs. Actual Direction"
            )

            chart = results.set_index("date")[
                ["actual", "prediction"]
            ]

            st.line_chart(chart)


            # --------------------------------------
            # Raw results
            # --------------------------------------

            with st.expander(
                "Show backtest results"
            ):

                st.dataframe(
                    results,
                    use_container_width=True,
                )


    except Exception as error:

        st.error(
            f"Something went wrong: {error}"
        )


else:

    st.info(
        "Enter a ticker and click **Analyze stock**."
    )