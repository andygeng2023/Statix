from __future__ import annotations

import streamlit as st

from src.config import MAX_SCAN

from src.storage.database import (
    enqueue_scan,
    job_status,
    latest_scan,
    get_settings,
)

from src.data.market import (
    history,
    quote,
)

from src.data.search import (
    security_name,
)

from src.ui.components import (
    card_row,
    t,
)


settings = get_settings()

lang = st.session_state.get(
    "language_preference",
    settings.get("language", "en"),
)


st.markdown("# Discover")

st.caption(
    "Model-ranked signals from the persistent scanner."
)


# ============================================================
# Scanner
# ============================================================

job, rows = latest_scan()

status = job_status()


limit = st.select_slider(
    "Universe size",
    options=[
        100,
        250,
        500,
        1000,
        1500,
        2000,
    ],
    value=500,
)


if st.button(
    t("queue", lang),
    type="primary",
):

    jid = enqueue_scan(
        limit
    )

    if jid:

        st.success(
            f"Scan job #{jid} queued."
        )

    else:

        st.error(
            "Persistent storage is unavailable."
        )


if status:

    st.caption(
        f"Job #{status.id}: "
        f"{status.status}"
    )


# ============================================================
# Latest scanner results
# ============================================================

if job and rows:

    st.subheader(
        t("latest", lang)
    )

    items = []

    for row in rows[:24]:

        ticker = str(
            row["ticker"]
        ).upper()

        try:

            q = quote(
                ticker
            )

            df = history(
                ticker,
                "6mo",
            )

            items.append(
                {
                    "ticker": ticker,
                    "name": security_name(
                        ticker
                    ),
                    "price": q.get(
                        "price",
                        row.get("price"),
                    ),
                    "change_pct": q.get(
                        "change_pct",
                        row.get(
                            "change_pct"
                        ),
                    ),
                    "df": df,
                    "signal": row.get(
                        "signal"
                    ),
                    "confidence": row.get(
                        "confidence"
                    ),
                    "reliability": row.get(
                        "reliability"
                    ),
                    "expected_return": row.get(
                        "expected_return"
                    ),
                }
            )

        except Exception:
            continue


    card_row(
        items,
        row_key="discover_results",
    )

else:

    st.info(
        "No completed scan yet."
    )