import streamlit as st
from src.data.market import get_stock_data,get_quote
from src.models.features import create_features
from src.models.model import load_model
from src.storage.database import record_view,is_watched,add_to_watchlist,remove_from_watchlist
from src.ui.components import header,money,pct,prob,chart,signal_badge

st.session_state.setdefault("selected_ticker",None)
ticker=st.session_state.get("selected_ticker")
if not ticker:
    header("Stock","Search for a symbol to open its research view.")
    if st.button("Go to Search",type="primary"): st.switch_page("pages/search.py")
    st.stop()

ticker=ticker.upper(); record_view(ticker)
header(ticker,"Market context, recent price action, and the latest model outlook.")

@st.fragment(run_every="20s")
def live_panel():
    q=get_quote(ticker)
    if q.get("price") is None:
        st.warning(f"Market data is currently unavailable for {ticker}. Try again shortly.")
        if st.button("Refresh market data",key="refresh-market"): from src.data.market import clear_market_cache; clear_market_cache(); st.rerun()
        return
    a,b,c=st.columns([1.2,1,1])
    a.metric("Price",money(q["price"]),pct(q.get("change_pct")))
    b.caption("Quote status"); b.write("Connected")
    if is_watched(ticker):
        if c.button("Remove from watchlist",use_container_width=True): remove_from_watchlist(ticker); st.rerun()
    else:
        if c.button("Add to watchlist",use_container_width=True): add_to_watchlist(ticker); st.rerun()

    df=get_stock_data(ticker,period="5y")
    if df.empty:
        st.warning("Historical price data is unavailable for this symbol."); return
    st.subheader("Price history")
    chart(df)

    model=load_model()
    if model is None:
        st.info("The trained production model is not installed yet. Complete the training step in the deployment guide.")
        return
    market=get_stock_data("SPY",period="5y")
    feat,_=create_features(df,market,horizon=5,include_target=False)
    missing=[c for c in model.feature_columns if c not in feat.columns]
    if missing:
        st.error("The model and feature pipeline are out of sync. Retrain the model with the current release."); return
    if len(feat)<64:
        st.warning("Not enough recent observations for the temporal model."); return
    X=feat[model.feature_columns].tail(64).to_numpy(dtype="float32")
    pred=model.predict(X)
    st.subheader("Model outlook")
    c1,c2,c3,c4=st.columns(4)
    with c1: st.caption("Signal"); signal_badge(pred["direction"])
    c2.metric("Confidence",prob(pred["confidence"]))
    c3.metric("Expected 5D return",pct(pred["expected_return"]*100))
    c4.metric("Reliability",prob(pred["reliability"]))
    st.progress(float(pred["reliability"]),text="Model reliability")
    st.caption("Reliability combines model confidence with validation performance. It is not a probability that the forecast will be correct.")
    st.caption("Signal distribution")
    st.dataframe({"Signal":list(pred["class_probabilities"].keys()),"Probability":[f"{v*100:.1f}%" for v in pred["class_probabilities"].values()]},hide_index=True,use_container_width=True)
    m=model.metrics
    st.caption(f"Model {m.get('model_version','unknown')} · validation accuracy {m.get('validation_accuracy','—')} · validation RMSE {m.get('validation_rmse','—')} · training rows {m.get('training_rows','—')}")

live_panel()
