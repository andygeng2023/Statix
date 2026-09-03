import streamlit as st
import plotly.graph_objects as go

def header(title,subtitle=""):
    st.markdown(f'<div class="page-title">{title}</div>',unsafe_allow_html=True)
    if subtitle: st.markdown(f'<div class="page-subtitle">{subtitle}</div>',unsafe_allow_html=True)
def money(v): return "—" if v is None else f"${float(v):,.2f}"
def pct(v): return "—" if v is None else f"{float(v):+.2f}%"
def prob(v): return "—" if v is None else f"{float(v)*100:.1f}%"
def chart(df):
    if df is None or df.empty: return
    d=df.tail(180)
    fig=go.Figure(go.Scatter(x=d.index,y=d.close,mode="lines",line=dict(width=2)))
    fig.update_layout(height=320,margin=dict(l=0,r=0,t=8,b=8),showlegend=False,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor="rgba(128,128,128,.12)"))
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False,"responsive":True})

def signal_badge(direction):
    cls="statix-positive" if "bullish" in direction.lower() else "statix-negative" if "bearish" in direction.lower() else ""
    st.markdown(f'<div class="statix-value {cls}">{direction}</div>',unsafe_allow_html=True)
