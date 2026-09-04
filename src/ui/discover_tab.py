import streamlit as st
import pandas as pd
from src.storage.database import enqueue_scan,latest_scan,job_status
from src.config import MAX_SCAN
from src.ui.components import t,money,pct

st.markdown("# Discover")
st.caption("The scanner runs outside Streamlit in a persistent worker and writes results to PostgreSQL.")
job,rows=latest_scan(); status=job_status()
limit=st.select_slider("Universe size",options=[100,250,500,1000,1500,2000],value=500)
if st.button(t("queue",lang),type="primary"):
 jid=enqueue_scan(limit)
 if jid: st.success(f"Scan job #{jid} queued.")
 else: st.error("Persistent storage is unavailable.")
 if status: st.caption(f"Job #{status.id}: {status.status}")
if job and rows:
 st.subheader(t("latest",lang))
 cols=st.columns(3)
 for i,r in enumerate(rows[:12]):
  with cols[i%3]:
   with st.container(border=True):
    st.markdown(f"### {r['ticker']}"); st.write(r["signal"]); st.metric(t("expected",lang),f"{r['expected_return']*100:+.2f}%",f"{r['change_pct']:+.2f}%" if r['change_pct'] is not None else None); st.progress(float(r["reliability"])); st.caption(f"Confidence {r['confidence']*100:.0f}% · {r['provider'] or '—'}")
else: st.info("No completed scan yet.")
