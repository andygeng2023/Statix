import streamlit as st
from pathlib import Path
import yfinance as yf
import pandas as pd
from src.models.model import load_model
from src.models.features import create_features
from src.ui.components import header
from src.config import ROOT,MAX_SCAN

header("Scanner","Screen the configured universe and rank the strongest model outputs.")
model=load_model()
if model is None:
    st.info("The scanner becomes available after the production model is trained."); st.stop()
uf=ROOT/"training"/"universe.txt"
tickers=[x.strip().upper() for x in uf.read_text().splitlines() if x.strip() and not x.startswith("#")][:MAX_SCAN]
limit=st.number_input("Scan up to",min_value=25,max_value=min(MAX_SCAN,len(tickers)),value=min(250,len(tickers)),step=25)
if st.button("Run scan",type="primary"):
    rows=[]; selected=tickers[:int(limit)]
    progress=st.progress(0,text="Starting scan…")
    for start in range(0,len(selected),50):
        batch=selected[start:start+50]
        try:
            raw=yf.download(batch,period="6mo",interval="1d",auto_adjust=True,progress=False,threads=True,group_by="ticker")
        except Exception:
            progress.progress(min(1,(start+len(batch))/len(selected)),text=f"Processed {start+len(batch):,}/{len(selected):,}")
            continue
        for t in batch:
            try:
                if not isinstance(raw.columns,pd.MultiIndex) or t not in raw.columns.get_level_values(0): continue
                d=raw[t].rename(columns=str.lower)
                d=d[["open","high","low","close","volume"]].dropna()
                f,_=create_features(d,None,include_target=False)
                if len(f)<64: continue
                X=f[model.feature_columns].tail(64).to_numpy(dtype="float32")
                p=model.predict(X)
                rows.append({"Ticker":t,"Signal":p["direction"],"Confidence":p["confidence"],"Reliability":p["reliability"],"Expected 5D":p["expected_return"]})
            except Exception:
                continue
        progress.progress(min(1,(start+len(batch))/len(selected)),text=f"Processed {start+len(batch):,}/{len(selected):,}")
    if rows:
        out=pd.DataFrame(rows).sort_values(["Reliability","Confidence","Expected 5D"],ascending=False).head(25)
        display=out.copy(); display["Confidence"]=display["Confidence"].map(lambda x:f"{x*100:.1f}%"); display["Reliability"]=display["Reliability"].map(lambda x:f"{x*100:.1f}%"); display["Expected 5D"]=display["Expected 5D"].map(lambda x:f"{x*100:+.2f}%")
        st.dataframe(display,hide_index=True,use_container_width=True)
        st.caption("Scanner results are a research shortlist, not automatic investment recommendations.")
    else: st.warning("No symbols returned enough usable data.")
