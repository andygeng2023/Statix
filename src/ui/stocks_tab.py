from __future__ import annotations

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.data.market import history, quote
from src.data.search import (
    search_stocks,
    security_name,
)
from src.data.news import latest_news
from src.models.features import create_features
from src.models.model import load_model
from src.storage.database import (
    add_to_watchlist,
    get_settings,
    get_watchlist,
    is_watched,
    record_view,
    remove_from_watchlist,
)
from src.ui.components import (
    card_row,
    money,
    pct,
    score,
    t,
)


RANGE_PERIODS = {
    "1D": 1,
    "5D": 5,
    "10D": 10,
    "1M": 31,
    "1Y": 365,
    "5Y": 1825,
    "10Y": 3650,
    "20Y": 7300,
    "10Y": 3650,
}


def _display_frame(
    frame,
    selected_range,
):
    if selected_range == "Auto":
        return frame

    if frame is None or frame.empty:
        return frame

    cutoff = (
        frame.index[-1]
        - pd.Timedelta(
            days=RANGE_PERIODS[
                selected_range
            ]
        )
    )

    return frame.loc[
        frame.index >= cutoff
    ]


def _chart_layout(
    fig,
    height,
):
    fig.update_layout(
        height=height,

        margin=dict(
            l=8,
            r=8,
            t=8,
            b=8,
        ),

        showlegend=False,
        hovermode="x unified",
        dragmode="pan",

        yaxis=dict(
            tickformat=".2f",
            fixedrange=False,
        ),

        xaxis=dict(
            fixedrange=False,
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        font=dict(
            size=12,
        ),
    )

    return fig


def _chart_config():
    return {
        "displayModeBar": True,
        "scrollZoom": True,
        "responsive": True,
        "modeBarButtonsToRemove": [
            "select2d",
            "lasso2d",
            "autoScale2d",
        ],
    }


settings = get_settings()

lang = st.session_state.get(
    "language_preference",
    settings.get(
        "language",
        "en",
    ),
)


st.markdown(
    f"# {t('stocks', lang)}"
)


# =========================================================
# SEARCH
# =========================================================

search = st.text_input(
    t("search", lang),
    placeholder=(
        "Apple, NVDA, 000001..."
    ),
)


if search.strip():

    results = search_stocks(
        search
    )

    if not results:

        st.info(
            t(
                "no_results",
                lang,
            )
        )

    else:

        items = []

        for result in results[:16]:

            symbol = result[
                "symbol"
            ].upper()
            current_quote = quote(symbol)

            items.append(
                {
                    "ticker": symbol,
                    "name": (
                        result.get(
                            "name"
                        )
                        or security_name(
                            symbol
                        )
                    ),
                    "price": current_quote.get("price"),
                    "change_pct": current_quote.get("change_pct"),
                    "df": None,
                }
            )

        st.caption(
            f"{len(items)} "
            f"{t('relevant_results', lang)}"
        )

        card_row(
            items,
            key_prefix="stocks_search",
        )
        if any(item.get("price") is None for item in items):
            if st.button("Refresh search quotes", key="refresh_search_quotes"):
                st.cache_data.clear()
                st.rerun()


st.divider()


# =========================================================
# WATCHLIST
# =========================================================

st.subheader(
    t("watchlist", lang)
)

watchlist = get_watchlist()


if not watchlist:

    st.info(
        t(
            "search_watchlist",
            lang,
        )
    )

else:

    items = []

    for ticker in watchlist:

        q = quote(ticker)

        items.append(
            {
                "ticker": ticker,
                "name": security_name(
                    ticker
                ),
                "price": q.get(
                    "price"
                ),
                "change_pct": q.get(
                    "change_pct"
                ),
                "df": history(
                    ticker,
                    "1y",
                ),
            }
        )

    card_row(
        items,
        key_prefix="stocks_watchlist",
    )


# =========================================================
# SELECTED STOCK
# =========================================================

ticker = st.session_state.get(
    "selected_ticker"
)


if not ticker:

    st.info(
        t(
            "select_stock",
            lang,
        )
    )

    st.stop()


record_view(ticker)


q = quote(ticker)

df = history(
    ticker,
    "10y",
)

name = security_name(
    ticker
)


st.divider()


# =========================================================
# STOCK HEADER
# =========================================================

title_col, action_col = st.columns(
    [5, 2],
    vertical_alignment="center",
)


with title_col:

    st.markdown(
        f"# {ticker}"
    )

    if (
        name
        and name.upper()
        != ticker.upper()
    ):
        st.caption(name)


watched = is_watched(
    ticker
)


with action_col:

    if watched:

        if st.button(
            t("remove", lang),
            key="detail_remove",
            use_container_width=True,
        ):

            remove_from_watchlist(
                ticker
            )

            st.rerun()

    elif st.button(
        t("watch", lang),
        key="detail_watch",
        type="primary",
        use_container_width=True,
    ):

        add_to_watchlist(
            ticker
        )

        st.rerun()


# =========================================================
# MARKET SNAPSHOT
# =========================================================

if q:

    a, b, c, d = st.columns(
        4
    )

    with a:
        st.metric(
            t("price", lang),
            money(
                q.get("price")
            ),
            pct(
                q.get(
                    "change_pct"
                )
            ),
        )

    with b:
        st.metric(
            "Open",
            money(
                q.get("open")
            ),
        )

    with c:
        st.metric(
            "High",
            money(
                q.get("high")
            ),
        )

    with d:
        st.metric(
            "Low",
            money(
                q.get("low")
            ),
        )


# =========================================================
# PRICE HISTORY
# =========================================================

if (
    df is not None
    and not df.empty
):

    st.subheader(
        t(
            "price_history",
            lang,
        )
    )

    range_choice = st.select_slider(
        "Displayed range",
        options=[
            "Auto",
            *RANGE_PERIODS,
        ],
        value="Auto",
        key=f"history_range_{ticker}",
    )

    displayed = _display_frame(
        df,
        range_choice,
    )

    if (
        displayed is not None
        and not displayed.empty
    ):

        st.caption(
            f"{displayed.index[0]:%Y-%m-%d} "
            f"to "
            f"{displayed.index[-1]:%Y-%m-%d} "
            f"· "
            f"{len(displayed)} sessions"
        )

        chart_data = displayed.copy()
        chart_data["sma_20"] = chart_data["close"].rolling(20, min_periods=1).mean()
        chart_data["sma_50"] = chart_data["close"].rolling(50, min_periods=1).mean()
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=chart_data.index,
            open=chart_data["open"], high=chart_data["high"],
            low=chart_data["low"], close=chart_data["close"],
            name="OHLC", increasing_line_color="#198754", decreasing_line_color="#c2413b",
        ))
        fig.add_trace(go.Scatter(
            x=chart_data.index, y=chart_data["sma_20"], name="20D average",
            mode="lines", line=dict(width=1.5, color="#4159a8"),
        ))
        fig.add_trace(go.Scatter(
            x=chart_data.index, y=chart_data["sma_50"], name="50D average",
            mode="lines", line=dict(width=1.5, color="#b97916"),
        ))
        fig.add_trace(go.Bar(
            x=chart_data.index, y=chart_data["volume"], name="Volume",
            yaxis="y2", opacity=.18, marker_color="#526985",
        ))

        _chart_layout(
            fig,
            400,
        )
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
            yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Volume"),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config=_chart_config(),
            key=f"detail_chart_{ticker}",
        )

else:

    st.warning(
        t(
            "historical_unavailable",
            lang,
        )
    )


# =========================================================
# MODEL
# =========================================================

st.subheader(
    t("model", lang)
)
news_items = latest_news(ticker)
if news_items:
    st.subheader("Recent news")
    for item in news_items:
        st.markdown(
            f"- [{item['title']}]({item['url']}) `"
            f"{item['sentiment']}` · {item['publisher']} · {item['date']}"
        )

model = load_model()


if model is None:

    st.info(
        t(
            "no_model",
            lang,
        )
    )

elif (
    df is None
    or df.empty
):

    st.info(
        t(
            "prediction_data",
            lang,
        )
    )

else:

    market = history(
        "SPY",
        "10y",
    )

    features, _ = create_features(
        df,
        market,
        target=False,
    )

    missing = [
        x
        for x in model.feature_columns
        if x not in features.columns
    ]

    if missing:

        st.error(
            t(
                "model_mismatch",
                lang,
            )
        )

    elif features.empty:

        st.info(
            t(
                "not_enough_history",
                lang,
            )
        )

    else:

        try:

            X = (
                features.reindex(
                    columns=model.feature_columns
                )
                .tail(64)
                .to_numpy(
                    dtype=float
                )
            )

            prediction = model.predict(
                X
            )

            a, b, c, d = st.columns(
                4
            )

            with a:
                st.metric(
                    "Signal",
                    prediction[
                        "direction"
                    ],
                )

            with b:
                st.metric(
                    t(
                        "confidence",
                        lang,
                    ),
                    score(
                        prediction.get(
                            "confidence"
                        )
                    ),
                )

            with c:
                st.metric(
                    t(
                        "reliability",
                        lang,
                    ),
                    score(
                        prediction.get(
                            "reliability"
                        )
                    ),
                )

            with d:
                st.metric(
                    "Model-estimated return",
                    pct(
                        prediction.get(
                            "expected_return",
                            0,
                        )
                        * 100
                    ),
                )

            st.caption(
                t(
                    "forecast_note",
                    lang,
                )
            )

            horizon_rows = []
            for horizon, values in prediction.get("horizons", {}).items():
                horizon_rows.append({
                    "Horizon": horizon,
                    "Expected return": pct(values["expected_return"] * 100),
                    "Possible error": f"±{pct(values['error'] * 100, signed=False)}",
                    "Lower range": pct(values["lower"] * 100),
                    "Upper range": pct(values["upper"] * 100),
                })
            if horizon_rows:
                st.caption("Model-derived horizon projections; error uses held-out test RMSE.")
                st.dataframe(
                    pd.DataFrame(horizon_rows),
                    hide_index=True,
                    use_container_width=True,
                )

            last_close = float(
                df["close"].iloc[-1]
            )

            selected_horizon = st.selectbox(
                "Forecast horizon",
                list(prediction.get("horizons", {"5D": {}})),
                index=1 if "5D" in prediction.get("horizons", {}) else 0,
                key=f"forecast_horizon_{ticker}",
            )
            horizon_values = prediction.get("horizons", {}).get(selected_horizon, {})
            expected_return = float(horizon_values.get("expected_return", prediction.get("expected_return", 0)))
            forecast_error = float(horizon_values.get("error", 0))
            horizon_days = {"1D": 1, "5D": 5, "10D": 10, "1M": 21, "6M": 126, "1Y": 252, "5Y": 1260, "10Y": 2520, "20Y": 5040}.get(selected_horizon, 5)

            points = min(30, max(2, horizon_days))
            forecast_dates = pd.bdate_range(start=df.index[-1], periods=points + 1)[1:]

            # Ease toward the horizon estimate instead of drawing a perpetual
            # straight-line rise from one short-horizon regression output.
            denominator = 1.0 - np.exp(-1.0 / 0.35)
            progress_values = [
                (1.0 - np.exp(-(step / points) / 0.35)) / denominator
                for step in range(1, points + 1)
            ]
            forecast_values = [
                last_close * (1.0 + expected_return * progress)
                for progress in progress_values
            ]
            lower_values = [
                last_close * (1.0 + (expected_return - forecast_error) * progress)
                for progress in progress_values
            ]
            upper_values = [
                last_close * (1.0 + (expected_return + forecast_error) * progress)
                for progress in progress_values
            ]

            forecast_history = (
                _display_frame(
                    df,
                    range_choice,
                )
            )

            forecast_fig = go.Figure(
                go.Scatter(
                    x=forecast_history.index,
                    y=forecast_history[
                        "close"
                    ],
                    mode="lines",
                    line=dict(
                        width=2,
                    ),
                    name="History",
                    hovertemplate=(
                        "%{x|%Y-%m-%d}"
                        "<br>$%{y:.2f}"
                        "<extra></extra>"
                    ),
                )
            )

            forecast_fig.add_trace(
                go.Scatter(
                    x=[
                        df.index[-1],
                        *forecast_dates,
                    ],
                    y=[
                        last_close,
                        *forecast_values,
                    ],
                    mode="lines+markers",
                    line=dict(
                        width=2,
                        dash="dash",
                    ),
                    marker=dict(
                        size=5,
                    ),
                    name="Model forecast",
                    hovertemplate=(
                        "%{x|%Y-%m-%d}"
                        "<br>$%{y:.2f}"
                        "<extra></extra>"
                    ),
                )
            )
            forecast_fig.add_trace(
                go.Scatter(
                    x=[df.index[-1], *forecast_dates],
                    y=[last_close, *lower_values],
                    mode="lines",
                    line=dict(width=1, dash="dot", color="#9aacc5"),
                    name="Lower estimate",
                    hovertemplate="%{x|%Y-%m-%d}<br>$%{y:.2f}<extra></extra>",
                )
            )
            forecast_fig.add_trace(
                go.Scatter(
                    x=[df.index[-1], *forecast_dates],
                    y=[last_close, *upper_values],
                    mode="lines",
                    line=dict(width=1, dash="dot", color="#9aacc5"),
                    name="Upper estimate",
                    hovertemplate="%{x|%Y-%m-%d}<br>$%{y:.2f}<extra></extra>",
                )
            )
            forecast_fig.add_trace(
                go.Scatter(
                    x=[*forecast_dates, *forecast_dates[::-1]],
                    y=[*upper_values, *lower_values[::-1]],
                    fill="toself",
                    fillcolor="rgba(185,121,22,.14)",
                    line=dict(color="rgba(0,0,0,0)"),
                    hoverinfo="skip",
                    name="Possible error range",
                )
            )

            _chart_layout(
                forecast_fig,
                360,
            )

            forecast_fig.update_layout(
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.01,
                    xanchor="left",
                    x=0,
                ),
            )

            st.subheader(
                t(
                    "model_outlook",
                    lang,
                )
            )

            st.plotly_chart(
                forecast_fig,
                use_container_width=True,
                config=_chart_config(),
                key=f"forecast_chart_{ticker}",
            )

        except Exception as exc:

            st.warning(
                f"{t('prediction_unavailable', lang)} "
                f"for {ticker}: {exc}"
            )