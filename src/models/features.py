from __future__ import annotations
import numpy as np
import pandas as pd
from src.config import FEATURE_VERSION

def rsi(s, n=14):
    d=s.diff(); up=d.clip(lower=0); dn=-d.clip(upper=0)
    au=up.ewm(alpha=1/n,adjust=False,min_periods=n).mean(); ad=dn.ewm(alpha=1/n,adjust=False,min_periods=n).mean()
    rs=au/ad.replace(0,np.nan); return 100-100/(1+rs)

def create_features(stock, market=None, horizon=5, include_target=True):
    df=stock.copy().sort_index()
    close=df["close"].astype(float); vol=df["volume"].astype(float)
    for n in [1,2,3,5,10,20,60]: df[f"ret_{n}"]=close.pct_change(n)
    for n in [10,20,50,100,200]: df[f"ma_{n}"]=close/close.rolling(n).mean()
    dr=close.pct_change()
    for n in [5,10,20,60]: df[f"vol_{n}"]=dr.rolling(n).std()
    for n in [7,14,21]: df[f"rsi_{n}"]=rsi(close,n)/100
    tr=pd.concat([(df.high-df.low),(df.high-close.shift()).abs(),(df.low-close.shift()).abs()],axis=1).max(axis=1)
    df["atr_pct"]=tr.rolling(14).mean()/close
    ema12=close.ewm(span=12,adjust=False).mean(); ema26=close.ewm(span=26,adjust=False).mean(); macd=ema12-ema26
    df["macd_pct"]=macd/close; df["macd_signal_pct"]=macd.ewm(span=9,adjust=False).mean()/close
    mid=close.rolling(20).mean(); sd=close.rolling(20).std(); df["bb_width"]=(4*sd/mid); df["bb_pos"]=(close-(mid-2*sd))/(4*sd)
    df["range_pct"]=(df.high-df.low)/close; df["gap_pct"]=df.open/close.shift()-1; df["volume_change"]=vol.pct_change(); df["volume_z"]=(vol-vol.rolling(20).mean())/vol.rolling(20).std()
    if market is not None and not market.empty:
        m=market["close"].astype(float); df["market_ret_5"]=m.pct_change(5).reindex(df.index); df["market_ret_20"]=m.pct_change(20).reindex(df.index); df["relative_ret_5"]=df["ret_5"]-df["market_ret_5"]
    else:
        df["market_ret_5"]=0.0; df["market_ret_20"]=0.0; df["relative_ret_5"]=df["ret_5"]
    if include_target:
        future=close.shift(-horizon)/close-1
        df["future_return"]=future
        df["target"]=pd.cut(future,[-np.inf,-0.03,-0.005,0.005,0.03,np.inf],labels=[0,1,2,3,4]).astype("float")
    feature_cols=[c for c in df.columns if c not in {"open","high","low","close","volume","future_return","target"}]
    clean=df.dropna(subset=feature_cols).copy()
    return clean, feature_cols
