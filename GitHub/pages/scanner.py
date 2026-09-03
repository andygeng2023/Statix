import streamlit as st
from pathlib import Path
import yfinance as yf
import pandas as pd
import numpy as np
from src.models.model import load_model
from src.models.features import create_features
from src.ui.components import header,pct
from src.config import ROOT
header("Scanner","Ranks a universe using the trained global model. Large scans are intentionally cached.")
model=load_model()
if model is None: st.warning("Train the model first."); st.stop()
uf=ROOT/"training"/"universe.txt"
tickers=[x.strip().upper() for x in uf.read_text().splitlines() if x.strip() and not x.startswith("#")]
limit=st.number_input("Scan up to",min_value=25,max_value=min(2000,len(tickers)),value=min(200,len(tickers)),step=25)
if st.button("Run scan",type="primary"):
    rows=[]; selected=tickers[:int(limit)]
    with st.spinner(f"Scanning {len(selected):,} symbols…"):
        for start in range(0,len(selected),50):
            batch=selected[start:start+50]
            try:
                raw=yf.download(batch,period="1y",interval="1d",auto_adjust=True,progress=False,threads=True,group_by="ticker")
            except Exception: continue
            for t in batch:
                try:
                    if isinstance(raw.columns,pd.MultiIndex) and t in raw.columns.get_level_values(0):
                        d=raw[t].rename(columns=str.lower)[["open","high","low","close","volume"]].dropna()
                    else: continue
                    f,_=create_features(d,None,include_target=False); X=f[model["feature_columns"]].tail(1)
                    if X.empty: continue
                    p=model["model"].predict(X); rows.append({"Ticker":t,"Signal":p["direction"],"Confidence":p["confidence"],"Expected 5D":p["expected_return"]})
                except Exception: pass
    if rows:
        out=pd.DataFrame(rows).sort_values(["Confidence","Expected 5D"],ascending=False).head(25)
        out["Confidence"]=out["Confidence"].map(lambda x:f"{x*100:.1f}%"); out["Expected 5D"]=out["Expected 5D"].map(lambda x:f"{x*100:+.2f}%")
        st.dataframe(out,hide_index=True,use_container_width=True)
    else: st.error("No symbols returned usable data.")
