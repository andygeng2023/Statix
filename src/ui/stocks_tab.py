from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data.market import history, quote
from src.data.search import search_stocks, security_name
from src.models.features import create_features
from src.models.model import load_model
from src.storage.database import (
    add_to_watchlist, get_settings, get_watchlist, is_watched, record_view,
    remove_from_watchlist,
)
from src.ui.components import card_row, money, pct, score, t

RANGE_PERIODS = {"1D": 1, "5D": 5, "10D": 10, "1M": 31, "1Y": 365, "5Y": 1825, "10Y": 3650}


def _display_frame(frame, selected_range):
    if selected_range == "Auto":
        return frame
    cutoff = frame.index[-1] - pd.Timedelta(days=RANGE_PERIODS[selected_range])
    return frame.loc[frame.index >= cutoff]


def _chart_layout(fig, height):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=10, b=10),
        showlegend=False,
        hovermode="x unified",
        dragmode="pan",
        yaxis=dict(tickformat=".2f"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _chart_config():
    return {
        "displayModeBar": True,
        "scrollZoom": True,
        "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
    }

settings = get_settings()
lang = st.session_state.get("language_preference", settings.get("language", "en"))

st.markdown(f"# {t('stocks', lang)}")
search = st.text_input(t("search", lang), placeholder="Apple, NVDA, 000001...")

if search.strip():
    results = search_stocks(search)
    if not results:
        st.info(t("no_results", lang))
    else:
        items = []
        for result in results[:16]:
            symbol = result["symbol"].upper()
            q = quote(symbol)
            items.append({
                "ticker": symbol,
                "name": result.get("name") or security_name(symbol),
                "price": q.get("price"),
                "change_pct": q.get("change_pct"),
                "df": history(symbol, "3mo"),
            })
        st.caption(f"{len(items)} {t('relevant_results', lang)}")
        card_row(
        items,
        key_prefix="stocks_search",
    )

st.divider()
st.subheader(t("watchlist", lang))
watchlist = get_watchlist()
if not watchlist:
    st.info(t("search_watchlist", lang))
else:
    items = []
    for ticker in watchlist:
        items.append({
            "ticker": ticker,
            "name": security_name(ticker),
            "price": quote(ticker).get("price"),
            "change_pct": quote(ticker).get("change_pct"),
            "df": history(ticker, "1y"),
        })
    card_row(
        items,
        key_prefix="stocks_watchlist",
    )

# Whole-card links set this value through the query string, so the detail view
# remains inside Statix rather than opening another browser tab.
ticker = st.session_state.get("selected_ticker")
if not ticker:
    st.info(t("select_stock", lang))
    st.stop()

record_view(ticker)
st.divider()
q = quote(ticker)
df = history(ticker, "10y")
name = security_name(ticker)

title_col, action_col = st.columns([5, 2], vertical_alignment="center")
with title_col:
    st.markdown(f"# {ticker}")
    if name and name.upper() != ticker.upper():
        st.caption(name)

watched = is_watched(ticker)
with action_col:
    if watched:
        if st.button(t("remove", lang), key="detail_remove", use_container_width=True):
            remove_from_watchlist(ticker)
            st.rerun()
    elif st.button(t("watch", lang), key="detail_watch", type="primary", use_container_width=True):
        add_to_watchlist(ticker)
        st.rerun()

if q:
    a, b, c, d = st.columns(4)
    with a: st.metric(t("price", lang), money(q.get("price")), pct(q.get("change_pct")))
    with b: st.metric("Open", money(q.get("open")))
    with c: st.metric("High", money(q.get("high")))
    with d: st.metric("Low", money(q.get("low")))

if df is not None and not df.empty:
    st.subheader(t("price_history", lang))
    range_choice = st.select_slider(
        "Displayed range", options=["Auto", *RANGE_PERIODS], value="Auto",
        key=f"history_range_{ticker}",
    )
    displayed = _display_frame(df, range_choice)
    st.caption(f"{displayed.index[0]:%Y-%m-%d} to {displayed.index[-1]:%Y-%m-%d} ({len(displayed)} sessions)")
    fig = go.Figure(go.Scatter(x=displayed.index, y=displayed["close"], mode="lines", line=dict(width=2), hovertemplate="%{x|%Y-%m-%d}<br>$%{y:.2f}<extra></extra>"))
    _chart_layout(fig, 400)
    st.plotly_chart(fig, use_container_width=True, config=_chart_config(), key=f"detail_chart_{ticker}")
else:
    st.warning(t("historical_unavailable", lang))

st.subheader(t("model", lang))
model = load_model()
if model is None:
    st.info(t("no_model", lang))
elif df is None or df.empty:
    st.info(t("prediction_data", lang))
else:
    market = history("SPY", "10y")
    features, _ = create_features(df, market, target=False)
    missing = [x for x in model.feature_columns if x not in features.columns]
    if missing:
        st.error(t("model_mismatch", lang))
    elif len(features) < 64:
        st.info(t("not_enough_history", lang))
    else:
        try:
            X = features[model.feature_columns].tail(64).to_numpy(dtype=float)
            prediction = model.predict(X)
            a, b, c, d = st.columns(4)
            with a: st.metric("Signal", prediction["direction"])
            with b: st.metric(t("confidence", lang), score(prediction.get("confidence")))
            with c: st.metric(t("reliability", lang), score(prediction.get("reliability")))
            with d: st.metric(t("expected", lang), pct(prediction.get("expected_return", 0) * 100))
            st.caption(t("forecast_note", lang))

            last_close = float(df["close"].iloc[-1])
            expected_return = float(prediction.get("expected_return", 0))
            forecast_dates = pd.bdate_range(start=df.index[-1], periods=6)[1:]
            forecast_values = [
                last_close + (last_close * expected_return * step / 5)
                for step in range(1, 6)
            ]
            forecast_history = _display_frame(df, range_choice)
            forecast_fig = go.Figure(
                go.Scatter(
                    x=forecast_history.index, y=forecast_history["close"],
                    mode="lines", line=dict(width=2, color="#4159a8"),
                    name="History", hovertemplate="%{x|%Y-%m-%d}<br>$%{y:.2f}<extra></extra>",
                )
            )
            forecast_fig.add_trace(go.Scatter(
                    x=[df.index[-1], *forecast_dates],
                    y=[last_close, *forecast_values],
                    mode="lines+markers",
                    line=dict(width=2, dash="dash", color="#d97706"),
                    marker=dict(size=5), name="Forecast",
                    hovertemplate="%{x|%Y-%m-%d}<br>$%{y:.2f}<extra></extra>",
                ))
            _chart_layout(forecast_fig, 360)
            forecast_fig.update_layout(showlegend=True)
            st.subheader(t("model_outlook", lang))
            st.plotly_chart(
                forecast_fig,
                use_container_width=True,
                config=_chart_config(),
                key=f"forecast_chart_{ticker}",
            )
        except Exception as exc:
            st.warning(f"{t('prediction_unavailable', lang)} for {ticker}: {exc}")
