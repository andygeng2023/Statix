from __future__ import annotations
from datetime import datetime, timezone
import os, requests
import pandas as pd
import yfinance as yf

PROVIDERS=["auto","akshare","quantdash","tushare","yfinance"]

def _secret(n,d=None):
    try:
        import streamlit as st; return st.secrets.get(n,d)
    except Exception: return os.getenv(n,d)

def selected_provider():
    try:
        import streamlit as st
        session_provider = st.session_state.get("provider_preference")
        if session_provider:
            return str(session_provider).lower()
    except Exception:
        pass
    return str(_secret("provider",os.getenv("STATIX_PROVIDER","auto"))).lower()

def _norm(df):
    if df is None or df.empty: return pd.DataFrame()
    df=df.copy()
    ren={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume","日期":"date","开盘":"open","最高":"high","最低":"low","收盘":"close","成交量":"volume","trade_date":"date"}
    df=df.rename(columns=ren)
    if "date" in df.columns: df=df.set_index(pd.to_datetime(df["date"],errors="coerce"))
    if not isinstance(df.index,pd.DatetimeIndex): df.index=pd.to_datetime(df.index,errors="coerce")
    need=["open","high","low","close","volume"]
    if not all(c in df.columns for c in need): return pd.DataFrame()
    df[need]=df[need].apply(pd.to_numeric,errors="coerce")
    return df[need].dropna(subset=["close"]).sort_index()

def quantdash_cfg():
    return _secret("quantdash_base_url","").rstrip("/"),_secret("quantdash_api_key","")

def _qd(path, params):
    base,key=quantdash_cfg()
    if not base: return {}
    h={"Authorization":f"Bearer {key}"} if key else {}
    try:
        r=requests.get(base+path,params=params,headers=h,timeout=8); r.raise_for_status(); return r.json()
    except Exception: return {}

def quantdash_quote(t):
    path=_secret("quantdash_quote_path","/v1/quote")
    d=_qd(path,{"symbol":t.upper()})
    d=d.get("data",d) if isinstance(d,dict) else {}
    p=d.get("price",d.get("last",d.get("close")))
    if p is None:return {}
    return {"ticker":t.upper(),"price":float(p),"change_pct":float(d["change_pct"]) if d.get("change_pct") is not None else None,"updated_at":d.get("timestamp") or datetime.now(timezone.utc).isoformat(),"provider":"quantdash"}

def quantdash_history(t,limit=1500):
    path=_secret("quantdash_history_path","/v1/history")
    d=_qd(path,{"symbol":t.upper(),"limit":min(limit,5000),"interval":"1d"})
    rows=d.get("data",d.get("bars",[])) if isinstance(d,dict) else []
    return _norm(pd.DataFrame(rows))

def akshare_history(t,limit=1500):
    try:
        import akshare as ak
        sym=t.upper().replace(".SH","").replace(".SZ","")
        if sym.isdigit():
            x=ak.stock_zh_a_hist(symbol=sym,period="daily",adjust="qfq")
            return _norm(x.tail(limit))
        x=ak.stock_us_daily(symbol=sym,adjust="qfq")
        return _norm(x.tail(limit))
    except Exception:return pd.DataFrame()

def akshare_quote(t):
    try:
        import akshare as ak
        sym=t.upper().replace(".SH","").replace(".SZ","")
        if not sym.isdigit(): return {}
        x=ak.stock_zh_a_spot_em(); row=x[x["代码"].astype(str)==sym]
        if row.empty:return {}
        r=row.iloc[0]; return {"ticker":t.upper(),"price":float(r["最新价"]),"change_pct":float(r["涨跌幅"]),"updated_at":datetime.now(timezone.utc).isoformat(),"provider":"akshare"}
    except Exception:return {}

def tushare_history(t,limit=1500):
    token=_secret("tushare_token","")
    if not token:return pd.DataFrame()
    try:
        import tushare as ts
        pro=ts.pro_api(token); code=t.upper()
        if "." not in code:
            code=code+".SH" if code.startswith("6") else code+".SZ"
        x=pro.daily(ts_code=code); return _norm(x.sort_values("trade_date").tail(limit))
    except Exception:return pd.DataFrame()

def tushare_quote(t): return {}

def yahoo_history(t,period="5y"): 
    try:
        raw=yf.download(t.upper(),period=period,interval="1d",auto_adjust=True,progress=False,threads=False)
        if raw is None or raw.empty:return pd.DataFrame()
        if isinstance(raw.columns,pd.MultiIndex): raw.columns=raw.columns.get_level_values(0)
        raw.columns=[str(c).lower() for c in raw.columns]; return _norm(raw)
    except Exception:return pd.DataFrame()

def yahoo_quote(t):
    try:
        fi=getattr(yf.Ticker(t.upper()),"fast_info",{}) or {}; p=fi.get("last_price") or fi.get("regular_market_price"); prev=fi.get("previous_close")
        if p is None:
            h=yahoo_history(t,"5d");
            if h.empty:return {}
            p=float(h.close.iloc[-1]); prev=float(h.close.iloc[-2]) if len(h)>1 else None
        ch=((float(p)-float(prev))/float(prev)*100) if prev not in (None,0) else None
        return {"ticker":t.upper(),"price":float(p),"change_pct":ch,"updated_at":datetime.now(timezone.utc).isoformat(),"provider":"yfinance"}
    except Exception:return {}

def _order():
    p=selected_provider(); return [p] if p!="auto" else ["quantdash","akshare","tushare","yfinance"]

def validate_symbol(t):
    """Cheap symbol validation used by search when provider search endpoints fail."""
    q = yahoo_quote(t)
    return bool(q)

def get_quote(t):
    funcs={"quantdash":quantdash_quote,"akshare":akshare_quote,"tushare":tushare_quote,"yfinance":yahoo_quote}
    for p in _order():
        q=funcs[p](t)
        if q:return q
    return {}

def get_history(t,period="5y",limit=1500):
    funcs={"quantdash":quantdash_history,"akshare":akshare_history,"tushare":tushare_history,"yfinance":lambda x,l:yahoo_history(x,period)}
    for p in _order():
        d=funcs[p](t,limit)
        if not d.empty:return d
    return pd.DataFrame()
