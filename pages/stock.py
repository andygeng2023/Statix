import streamlit as st
from src.data.market import get_stock_data,get_quote
from src.models.features import create_features
from src.models.model import load_model
from src.storage.database import record_view,is_watched,add_to_watchlist,remove_from_watchlist
from src.ui.components import header,money,pct,prob,chart

ticker=st.session_state.get("selected_ticker")
if not ticker:
    st.info("Choose a stock from Search.")
    if st.button("Go to Search"): st.switch_page("pages/search.py")
    st.stop()
record_view(ticker)
header(ticker,"Current market context and the latest model output.")

@st.fragment(run_every="20s")
def live_panel():
    q=get_quote(ticker)
    if q.get("price") is None:
        st.error(q.get("error","Market data unavailable.")); return
    col1,col2,col3=st.columns(3)
    col1.metric("Price",money(q["price"]))
    col2.metric("Daily change",pct(q.get("change_pct")))
    if is_watched(ticker):
        if col3.button("Remove from watchlist",use_container_width=True): remove_from_watchlist(ticker); st.rerun()
    else:
        if col3.button("Add to watchlist",use_container_width=True): add_to_watchlist(ticker); st.rerun()
    try: df=get_stock_data(ticker)
    except Exception as e: st.error(str(e)); return
    chart(df)
    model=load_model()
    if model is None:
        st.warning("The production model has not been trained yet. Run `python -m training.train`, then commit the generated artifact.")
        return
    try: market=get_stock_data("SPY")
    except Exception: market=None
    feat,_=create_features(df,market,horizon=5,include_target=False)
    missing=[c for c in model["feature_columns"] if c not in feat.columns]
    if missing:
        st.error("Model/data feature mismatch. Retrain the model with the current feature version."); return
    X=feat[model["feature_columns"]].tail(1)
    pred=model["model"].predict(X)
    a,b,c,d=st.columns(4)
    a.metric("Signal",pred["direction"]); b.metric("Confidence",prob(pred["confidence"])); c.metric("Expected 5D return",pct(pred["expected_return"]*100)); d.metric("Model agreement",prob(pred["model_agreement"]))
    st.caption("Signal probabilities")
    st.dataframe({"Signal":list(pred["class_probabilities"].keys()),"Probability":[f'{v*100:.1f}%' for v in pred["class_probabilities"].values()]},hide_index=True,use_container_width=True)
    m=model.get("metrics",{})
    st.caption(f"Model: {model.get('model_version','unknown')} · Test accuracy: {m.get('test_accuracy','—')} · Training rows: {m.get('training_rows','—')}")

live_panel()
