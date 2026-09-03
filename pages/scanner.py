import streamlit as st
import pandas as pd
from src.storage.database import enqueue_scan, latest_scan
from src.config import MAX_SCAN
from src.ui.components import header

header("Scanner","The scanner runs in a persistent worker and stores the latest ranked results in shared cache.")
job,rows=latest_scan()
limit=st.number_input("Universe size",min_value=25,max_value=MAX_SCAN,value=min(500,MAX_SCAN),step=25)
if st.button("Queue scan",type="primary"):
    jid=enqueue_scan(int(limit)); st.success(f"Scan queued (job #{jid}).")
    st.rerun()
if job:
    st.caption(f"Latest completed scan: {job.finished_at} · status: {job.status} · symbols requested: {job.limit}")
    if rows:
        out=pd.DataFrame(rows); out["Confidence"]=out["Confidence"].map(lambda x:f"{x*100:.1f}%");out["Reliability"]=out["Reliability"].map(lambda x:f"{x*100:.1f}%");out["Expected 5D"]=out["Expected 5D"].map(lambda x:f"{x*100:+.2f}%")
        st.dataframe(out,hide_index=True,use_container_width=True)
else:
    st.info("No completed scan yet. Queue one after the worker is running.")
st.caption("Results are model-generated research signals, not investment advice or guarantees.")
