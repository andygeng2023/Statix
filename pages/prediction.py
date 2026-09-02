import streamlit as st
import plotly.graph_objects as go

from src.data.market import get_stock_data, get_quote
from src.models.features import create_features
from src.models.ensemble import (
    train_and_predict,
    MODEL_VERSION,
)
from src.storage.database import (
    get_cached_prediction,
    save_viewed_prediction,
    save_prediction_history,
    add_to_watchlist,
    remove_from_watchlist,
    is_watched,
)


st.title("Prediction")

ticker = st.session_state.get("selected_ticker")

if not ticker:
    st.info("Choose a stock from Search first.")

    if st.button(
        "Search up a stock",
        use_container_width=True,
    ):
        st.switch_page("pages/search.py")

    st.stop()


ticker = ticker.upper().strip()

if st.button("Search up a different stock"):
    st.switch_page("pages/search.py")


st.header(ticker)

HORIZON = 5

# --------------------------------------------------
# Market data
# --------------------------------------------------

with st.status(
    "Loading historical market data...",
    expanded=False,
) as status:

    data = get_stock_data(
        ticker,
        period="5y",
        interval="1d",
    )

    market_data = get_stock_data(
        "SPY",
        period="5y",
        interval="1d",
    )

    if data.empty:
        status.update(
            label="Could not load market data.",
            state="error",
        )
        st.error(
            f"No usable historical market data was found for {ticker}."
        )
        st.stop()

    if len(data) < 120:
        status.update(
            label="Not enough historical data.",
            state="error",
        )
        st.error(
            f"{ticker} has only {len(data)} daily observations. "
            "Statix needs more historical data to make a reliable model."
        )
        st.stop()

    status.update(
        label="Market data loaded.",
        state="complete",
    )


latest_market_date = data.index[-1].strftime("%Y-%m-%d")
latest_price = float(data["Close"].iloc[-1])

quote = get_quote(ticker)

# --------------------------------------------------
# Cache
# --------------------------------------------------

cached = get_cached_prediction(
    ticker=ticker,
    market_date=latest_market_date,
    model_version=MODEL_VERSION,
    horizon=HORIZON,
)

if cached:

    prediction = cached

    st.success(
        "Loaded saved analysis. Statix did not retrain the model."
    )

else:

    with st.status(
        "Building prediction model...",
        expanded=False,
    ) as status:

        features, feature_columns = create_features(
            data,
            market_data,
            horizon=HORIZON,
        )

        if len(features) < 180:
            status.update(
                label="Not enough usable historical context.",
                state="error",
            )

            st.error(
                f"Statix could only create {len(features)} usable "
                "training rows after calculating all features. "
                "This stock needs more history."
            )
            st.stop()

        status.update(
            label="Training ensemble...",
            state="running",
        )

        try:
            prediction = train_and_predict(
                features,
                feature_columns,
                horizon=HORIZON,
            )

        except ValueError as error:
            status.update(
                label="Prediction unavailable.",
                state="error",
            )
            st.error(str(error))
            st.stop()

        save_viewed_prediction(
            ticker=ticker,
            market_date=latest_market_date,
            price=latest_price,
            prediction=prediction,
        )

        save_prediction_history(
            ticker=ticker,
            market_date=latest_market_date,
            price=latest_price,
            prediction=prediction,
        )

        status.update(
            label="Prediction complete.",
            state="complete",
        )


# --------------------------------------------------
# Overview
# --------------------------------------------------

st.divider()

price_col, change_col, signal_col = st.columns(3)

with price_col:
    st.metric(
        "Current Price",
        f"${latest_price:,.2f}",
    )

with change_col:
    if quote["change_pct"] is not None:
        st.metric(
            "Daily Change",
            f"{quote['change_pct']:+.2f}%",
        )
    else:
        st.metric(
            "Daily Change",
            "Unavailable",
        )

with signal_col:
    st.metric(
        "Statix Signal",
        prediction["direction"],
    )


st.divider()

a, b, c, d = st.columns(4)

with a:
    st.metric(
        "Probability Up",
        f"{prediction['probability_up'] * 100:.1f}%",
    )

with b:
    st.metric(
        "Expected 5D Return",
        f"{prediction['expected_return'] * 100:+.2f}%",
    )

with c:
    st.metric(
        "Confidence",
        f"{prediction['confidence'] * 100:.1f}%",
    )

with d:
    st.metric(
        "Validation Accuracy",
        f"{prediction['test_accuracy'] * 100:.1f}%",
    )


# --------------------------------------------------
# Watchlist
# --------------------------------------------------

if is_watched(ticker):

    if st.button(
        "Remove from Watchlist",
        use_container_width=True,
    ):
        remove_from_watchlist(ticker)
        st.rerun()

else:

    if st.button(
        "Add to Watchlist",
        use_container_width=True,
    ):
        add_to_watchlist(ticker)
        st.rerun()


# --------------------------------------------------
# Tabs
# --------------------------------------------------

overview_tab, prediction_tab, chart_tab = st.tabs(
    [
        "Overview",
        "Prediction",
        "Chart",
    ]
)


with overview_tab:

    st.subheader("Analysis")

    st.write(
        f"Market date: **{latest_market_date}**"
    )

    if prediction.get("cached"):
        st.caption(
            "This result was loaded from Statix's saved analysis."
        )
    else:
        st.caption(
            "This analysis was calculated from the latest available data."
        )


with prediction_tab:

    st.subheader("Model Output")

    st.write(
        f"Statix currently classifies **{ticker}** as "
        f"**{prediction['direction']}**."
    )

    st.write(
        f"The ensemble estimates a "
        f"**{prediction['probability_up'] * 100:.1f}%** probability "
        f"of a positive 5-day return."
    )

    st.write(
        f"Estimated 5-day return: "
        f"**{prediction['expected_return'] * 100:+.2f}%**"
    )

    st.caption(
        f"Model version: {prediction['model_version']}"
    )


with chart_tab:

    st.subheader("Price History")

    chart = go.Figure()

    chart.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name=ticker,
        )
    )

    chart.update_layout(
        height=600,
        xaxis_rangeslider_visible=False,
    )

    st.plotly_chart(
        chart,
        use_container_width=True,
    )