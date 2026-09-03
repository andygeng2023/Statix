import streamlit as st

from src.auth import (
    current_user_id,
    current_user_name,
)
from src.config import SETTINGS
from src.data.market import (
    clear_market_cache,
)


st.title(
    "Settings"
)


st.subheader(
    "Account"
)


st.write(
    f"User: **{current_user_name()}**"
)

st.caption(
    f"Internal user ID: "
    f"`{current_user_id()}`"
)


st.divider()


st.subheader(
    "System"
)


st.write(
    f"Market provider: "
    f"`{SETTINGS.market_provider}`"
)

st.write(
    f"Model version: "
    f"`{SETTINGS.model_version}`"
)

st.write(
    f"Feature version: "
    f"`{SETTINGS.feature_version}`"
)

st.write(
    f"Prediction horizon: "
    f"`{SETTINGS.prediction_horizon} trading days`"
)


st.divider()


st.subheader(
    "Cache"
)


st.write(
    "Market data is cached so repeated "
    "page reruns do not repeatedly request "
    "the same data."
)


if st.button(
    "Clear market cache",
):

    clear_market_cache()

    st.success(
        "Market cache cleared."
    )


st.divider()


st.subheader(
    "About Statix"
)


st.write(
    "Statix is an experimental market "
    "prediction research platform."
)

st.write(
    "Predictions are generated from "
    "historical market features and machine "
    "learning models. They are not guaranteed "
    "to be correct."
)