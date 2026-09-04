from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
from src.config import TEXT


def t(key, lang):
    return TEXT.get(lang, TEXT["en"]).get(key, TEXT["en"].get(key, key))


def money(v):
    return "—" if v is None else f"${float(v):,.2f}"


def pct(v):
    return "—" if v is None else f"{float(v):+.2f}%"


def sparkline(df, height=170):
    if df is None or df.empty:
        return
    fig = go.Figure(go.Scatter(
        x=df.index, y=df["close"], mode="lines",
        line={"width": 2},
        hovertemplate="%{x|%Y-%m-%d}<br>$%{y:.2f}<extra></extra>",
    ))
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=6, b=6),
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def stock_card(ticker, name, q, df=None, signal=None, lang="en", key_prefix="card"):
    with st.container(border=True):
        top, action = st.columns([4, 1])
        with top:
            st.markdown(f"### {name}")
            st.caption(ticker)
        with action:
            if st.button(
                t("analyze", lang),
                key=f"{key_prefix}_open_{ticker}",
                use_container_width=True,
            ):
                st.session_state["selected_ticker"] = ticker
                st.session_state["active_tab"] = "stocks"
                st.rerun()

        a, b, c = st.columns(3)
        a.metric(t("price", lang), money(q.get("price")))
        b.metric(t("change", lang), pct(q.get("change_pct")))
        c.metric(
            t("data_source", lang),
            q.get("provider", "—"),
        )

        sparkline(df, 150)

        if signal:
            a, b, c = st.columns(3)
            a.metric("Signal", signal["direction"])
            b.metric(t("confidence", lang), f'{signal["confidence"]*100:.1f}%')
            c.metric(t("reliability", lang), f'{signal["reliability"]*100:.1f}%')
            st.caption(f'{t("expected", lang)}: {signal["expected_return"]*100:+.2f}%')


def detail_chart(df):
    if df is None or df.empty:
        st.warning("Historical price data is unavailable.")
        return
    fig = go.Figure(go.Scatter(
        x=df.index, y=df["close"], mode="lines",
        name="Close",
        line={"width": 2},
    ))
    fig.update_layout(
        height=380,
        margin=dict(l=0, r=0, t=10, b=10),
        hovermode="x unified",
        xaxis_title="Date",
        yaxis_title="Price",
    )
    st.plotly_chart(fig, use_container_width=True)
