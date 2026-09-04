from __future__ import annotations
import numpy as np, pandas as pd
FEATURE_VERSION="statix-fast-features-v1"

def _rsi(s,n=14):
 d=s.diff(); up=d.clip(lower=0); down=-d.clip(upper=0); a=up.ewm(alpha=1/n,adjust=False,min_periods=n).mean(); b=down.ewm(alpha=1/n,adjust=False,min_periods=n).mean(); rs=a/b.replace(0,np.nan); return 100-100/(1+rs)

def create_features(stock,market=None,horizon=5,target=True):
 d=stock.copy().sort_index(); c=d.close.astype(float); v=d.volume.astype(float); r=c.pct_change()
 for n in [1,2,3,5,10,20,40,60]: d[f"ret_{n}"]=c.pct_change(n)
 for n in [10,20,50,100,200]: d[f"ma_{n}"]=c/c.rolling(n).mean()-1
 for n in [5,10,20,40,60]: d[f"vol_{n}"]=r.rolling(n).std()
 for n in [7,14,21]: d[f"rsi_{n}"]=_rsi(c,n)/100
 tr=pd.concat([d.high-d.low,(d.high-c.shift()).abs(),(d.low-c.shift()).abs()],axis=1).max(axis=1); d["atr_pct"]=tr.rolling(14).mean()/c
 e12=c.ewm(span=12,adjust=False).mean(); e26=c.ewm(span=26,adjust=False).mean(); mac=e12-e26; d["macd_pct"]=mac/c; d["macd_signal_pct"]=mac.ewm(span=9,adjust=False).mean()/c
 mid=c.rolling(20).mean(); sd=c.rolling(20).std(); d["bb_width"]=4*sd/mid; d["bb_pos"]=(c-(mid-2*sd))/(4*sd); d["range_pct"]=(d.high-d.low)/c; d["gap_pct"]=d.open/c.shift()-1
 vm=v.rolling(20).mean(); vs=v.rolling(20).std().replace(0,np.nan); d["volume_change"]=v.pct_change(); d["volume_z"]=(v-vm)/vs
 if market is not None and not market.empty:
  m=market.close.astype(float); d["market_ret_5"]=m.pct_change(5).reindex(d.index).ffill(); d["market_ret_20"]=m.pct_change(20).reindex(d.index).ffill()
 else: d["market_ret_5"]=0.; d["market_ret_20"]=0.
 d["relative_ret_5"]=d.ret_5-d.market_ret_5; d["relative_ret_20"]=d.ret_20-d.market_ret_20
 cols=[c for c in d.columns if c not in {"open","high","low","close","volume","future_return","target"}]
 if target:
  d["future_return"]=c.shift(-horizon)/c-1; d["target"]=pd.cut(d.future_return,[-np.inf,-.03,-.005,.005,.03,np.inf],labels=False).astype(float)
 clean=d.dropna(subset=cols+(["future_return","target"] if target else [])).copy(); return clean,cols
