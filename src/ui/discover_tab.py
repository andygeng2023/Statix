import streamlit as st

from src.storage.database import enqueue_scan, latest_scan, job_status
from src.ui.components import t
from src.data.search import resolve_name

lang = st.session_state.get("language_preference", "en")

st.title(t("discover", lang))
st.caption("Ranked model signals from the persistent scanner. Results are recommendations for research, not guarantees.")

job, rows = latest_scan()
status = job_status()

limit = st.select_slider(
    "Universe size",
    options=[100, 250, 500, 1000, 1500, 2000],
    value=500,
)

if st.button(t("queue", lang), type="primary"):
    jid = enqueue_scan(limit)
    if jid:
        st.success(f"Scan job #{jid} queued.")
    else:
        st.error("Persistent storage is unavailable.")

if status:
    st.caption(f"Job #{status.id}: {status.status}")

if job and rows:
    st.subheader(t("latest", lang))
    for i, row in enumerate(rows[:12]):
        ticker = row["ticker"]
        with st.container(border=True):
            a, b, c = st.columns([4, 1.5, 1.5])
            with a:
                st.markdown(f"### {resolve_name(ticker)}")
                st.caption(ticker)
                st.write(row["signal"])
            with b:
                st.metric(t("expected", lang), f'{row["expected_return"]*100:+.2f}%')
                st.metric(t("confidence", lang), f'{row["confidence"]*100:.1f}%')
            with c:
                st.metric(t("reliability", lang), f'{row["reliability"]*100:.1f}%')
                st.caption(row["provider"] or "—")
            if st.button("Open", key=f"discover_open_{i}_{ticker}", use_container_width=True):
                st.session_state["selected_ticker"] = ticker
                st.session_state["active_tab"] = "stocks"
                st.rerun()
else:
    st.info("No completed scan yet. Queue a scan and keep the worker running.")
