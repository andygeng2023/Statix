import streamlit as st
import plotly.graph_objects as go

def header(title, subtitle=""):
    st.markdown(f'<div class="page-title">{title}</div>',unsafe_allow_html=True)
    if subtitle: st.markdown(f'<div class="page-subtitle">{subtitle}</div>',unsafe_allow_html=True)
def money(v): return "—" if v is None else f"${float(v):,.2f}"
def pct(v): return "—" if v is None else f"{float(v):+.2f}%"
def prob(v): return "—" if v is None else f"{float(v)*100:.1f}%"
def chart(df):
    if df is None or df.empty: return
    d=df.tail(120); fig=go.Figure(go.Scatter(x=d.index,y=d.close,mode="lines")); fig.update_layout(height=280,margin=dict(l=0,r=0,t=10,b=10),showlegend=False); st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
