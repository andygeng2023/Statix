from __future__ import annotations

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

settings = get_settings()
lang = st.session_state.get("language_preference", settings.get("language", "en"))

st.markdown("# Stocks")
search = st.text_input(t("search", lang), placeholder="Apple, Aple, NVDA, 000001...")

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
        st.caption(f"{len(items)} relevant result(s)")
        card_row(
        items,
        key_prefix="stocks_search",
    )

st.divider()
st.subheader(t("watchlist", lang))
watchlist = get_watchlist()
if not watchlist:
    st.info("Search for a symbol to add it to your watchlist.")
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
    st.info("Select a stock by clicking any stock card.")
    st.stop()

record_view(ticker)
st.divider()
q = quote(ticker)
df = history(ticker, "5y")
name = security_name(ticker)

st.markdown(f"# {ticker}")
if name and name.upper() != ticker.upper():
    st.caption(name)

if q:
    a, b, c, d = st.columns(4)
    with a: st.metric(t("price", lang), money(q.get("price")), pct(q.get("change_pct")))
    with b: st.metric("Open", money(q.get("open")))
    with c: st.metric("High", money(q.get("high")))
    with d: st.metric("Low", money(q.get("low")))

if df is not None and not df.empty:
    st.subheader("Price history")
    fig = go.Figure(go.Scatter(x=df.index, y=df["close"], mode="lines", line=dict(width=2), hovertemplate="%{x|%Y-%m-%d}<br>$%{y:.2f}<extra></extra>"))
    fig.update_layout(height=400, margin=dict(l=8,r=8,t=10,b=10), showlegend=False, hovermode="x unified", yaxis=dict(tickformat=".2f"), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=f"detail_chart_{ticker}")
else:
    st.warning("Historical data is unavailable for this symbol.")

if is_watched(ticker):
    if st.button(t("remove", lang), key="detail_remove"):
        remove_from_watchlist(ticker); st.rerun()
else:
    if st.button(t("watch", lang), key="detail_watch", type="primary"):
        add_to_watchlist(ticker); st.rerun()

st.subheader(t("model", lang))
model = load_model()
if model is None:
    st.info(t("no_model", lang))
elif df is None or df.empty:
    st.info("Historical data is required for prediction.")
else:
    market = history("SPY", "5y")
    features, _ = create_features(df, market, target=False)
    missing = [x for x in model.feature_columns if x not in features.columns]
    if missing:
        st.error("The trained model does not match the current feature set. Retrain it.")
    elif len(features) < 64:
        st.info("Not enough recent history for a 64-day prediction window.")
    else:
        try:
            X = features[model.feature_columns].tail(64).to_numpy(dtype=float)
            prediction = model.predict(X)
            a, b, c, d = st.columns(4)
            with a: st.metric("Signal", prediction["direction"])
            with b: st.metric(t("confidence", lang), score(prediction.get("confidence")))
            with c: st.metric(t("reliability", lang), score(prediction.get("reliability")))
            with d: st.metric(t("expected", lang), pct(prediction.get("expected_return", 0) * 100))
        except Exception as exc:
            st.warning(f"Prediction unavailable for {ticker}: {exc}")
