from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def inject_css() -> None:

    st.markdown(
        """
        <style>
        .stock-card {
            border: 1px solid rgba(128,128,128,.18);
            border-radius: 16px;
            padding: 1rem;
            margin-bottom: .8rem;
            background: rgba(128,128,128,.035);
        }

        .stock-card-title {
            font-size: 1.1rem;
            font-weight: 800;
        }

        .stock-card-muted {
            color: #888;
            font-size: .78rem;
        }

        .signal {
            display: inline-block;
            padding: .22rem .55rem;
            border-radius: 999px;
            font-size: .75rem;
            font-weight: 700;
            border: 1px solid rgba(128,128,128,.2);
        }

        .page-title {
            font-size: 2.15rem;
            font-weight: 850;
            letter-spacing: -.045em;
            margin-bottom: .15rem;
        }

        .page-subtitle {
            color: #888;
            margin-bottom: 1.4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_money(
    value,
) -> str:

    if value is None:
        return "—"

    try:
        return f"${float(value):,.2f}"

    except Exception:
        return "—"


def format_percent(
    value,
    digits: int = 2,
) -> str:

    if value is None:
        return "—"

    try:

        return (
            f"{float(value):+.{digits}f}%"
        )

    except Exception:
        return "—"


def format_probability(
    value,
) -> str:

    if value is None:
        return "—"

    try:

        value = float(value)

        if value <= 1:
            value *= 100

        return f"{value:.1f}%"

    except Exception:
        return "—"


def format_confidence(
    value,
) -> str:

    if value is None:
        return "—"

    try:

        value = float(value)

        if value <= 1:
            value *= 100

        return f"{value:.0f}%"

    except Exception:
        return "—"


def mini_chart(
    data: pd.DataFrame,
) -> None:

    if (
        data is None
        or data.empty
        or "close" not in data.columns
    ):
        return

    chart_data = (
        data["close"]
        .dropna()
        .tail(90)
    )

    if chart_data.empty:
        return

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=chart_data.index,
            y=chart_data.values,
            mode="lines",
            line=dict(width=2),
            hovertemplate=(
                "$%{y:.2f}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=115,
        margin=dict(
            l=0,
            r=0,
            t=5,
            b=5,
        ),
        showlegend=False,
        xaxis=dict(
            visible=False,
            fixedrange=True,
        ),
        yaxis=dict(
            visible=False,
            fixedrange=True,
        ),
        hovermode="x unified",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False
        },
    )


def page_header(
    title: str,
    subtitle: str = "",
) -> None:

    st.markdown(
        f'<div class="page-title">{title}</div>',
        unsafe_allow_html=True,
    )

    if subtitle:

        st.markdown(
            f'<div class="page-subtitle">{subtitle}</div>',
            unsafe_allow_html=True,
        )


def signal_badge(
    signal: str,
) -> None:

    st.markdown(
        f'<span class="signal">{signal}</span>',
        unsafe_allow_html=True,
    )