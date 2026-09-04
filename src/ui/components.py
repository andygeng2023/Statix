import streamlit as st
import plotly.graph_objects as go
from src.config import TEXT

def t(key,lang):return TEXT.get(lang,TEXT["en"]).get(key,TEXT["en"].get(key,key))
def money(v):return "—" if v is None else f"${float(v):,.2f}"
def pct(v):return "—" if v is None else f"{float(v):+.2f}%"
def card(ticker,q,df=None,signal=None):
 with st.container(border=True):
  a,b=st.columns([1.7,1]); a.markdown(f"### {ticker}"); a.metric("Price",money(q.get("price")),pct(q.get("change_pct")))
  if signal: b.markdown(f"**{signal['direction']}**"); b.caption(f"{signal['confidence']*100:.0f}% confidence · {signal['reliability']*100:.0f}% reliability")
  if df is not None and not df.empty:
   fig=go.Figure(go.Scatter(x=df.index,y=df.close,mode="lines")); fig.update_layout(height=120,margin=dict(l=0,r=0,t=4,b=0),showlegend=False,xaxis=dict(visible=False),yaxis=dict(visible=False)); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
