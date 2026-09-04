import streamlit as st

from src.data.search import search_stocks, resolve_name
from src.data.market import quote, history
from src.storage.database import (
    get_watchlist, is_watched, add_to_watchlist,
    remove_from_watchlist, record_view,
)
from src.models.model import load_model
from src.models.features import create_features
from src.ui.components import stock_card, detail_chart, t

lang = st.session_state.get("language_preference", "en")
st.title(t("stocks", lang))

selected = st.session_state.get("selected_ticker")

# Search is intentionally cheap: it does not download price history for every result.
query = st.text_input(
    t("search", lang),
    placeholder="Apple, Aple, NVDA, 000001…",
)
if query:
    results = search_stocks(query)
    if not results:
        st.info(t("no_results", lang))
    for i, row in enumerate(results):
        symbol = row["symbol"]
        name = row.get("name") or symbol
        q = quote(symbol)
        with st.container(border=True):
            a, b, c = st.columns([4, 1.5, 1.2])
            with a:
                st.markdown(f"**{name}**")
                st.caption(f"{symbol} · {row.get('exchange', '')}")
            with b:
                st.metric(t("price", lang), q.get("price", "—"), pct_value(q.get("change_pct")))
            with c:
                if st.button(t("analyze", lang), key=f"search_open_{i}_{symbol}", use_container_width=True):
                    st.session_state["selected_ticker"] = symbol
                    st.session_state["active_tab"] = "stocks"
                    st.rerun()

st.divider()
st.subheader(t("watchlist", lang))

watchlist = get_watchlist()
if not watchlist:
    st.info("Add a stock from its analysis page.")

for ticker in watchlist:
    q = quote(ticker)
    df = history(ticker, "1y")
    # Watchlist uses exactly the same card surface as Home/Discover.
    stock_card(
        ticker,
        resolve_name(ticker),
        q,
        df=df,
        lang=lang,
        key_prefix="watch",
    )
    if st.button(t("remove", lang), key=f"watch_remove_{ticker}", use_container_width=True):
        remove_from_watchlist(ticker)
        st.rerun()

if selected:
    st.divider()
    name = resolve_name(selected)
    st.header(name)
    st.caption(selected)

    q = quote(selected)
    df = history(selected, "2y")

    if df.empty:
        st.error("No historical data was returned for this symbol.")
    else:
        last = float(df["close"].iloc[-1])
        prev = float(df["close"].iloc[-2]) if len(df) > 1 else None
        change = ((last - prev) / prev * 100) if prev else None
        a, b, c = st.columns(3)
        a.metric(t("price", lang), f"${last:,.2f}")
        b.metric(t("change", lang), f"{change:+.2f}%" if change is not None else "—")
        c.metric(t("data_source", lang), q.get("provider", "historical data"))
        detail_chart(df)

        if is_watched(selected):
            if st.button(t("remove", lang), key="detail_remove"):
                remove_from_watchlist(selected)
                st.rerun()
        else:
            if st.button(t("watch", lang), key="detail_watch", type="primary"):
                add_to_watchlist(selected)
                st.rerun()

        model = load_model()
        if model is None:
            st.warning(t("no_model", lang))
        else:
            market = history("SPY", "2y")
            f, _ = create_features(df, market, target=False)
            if len(f) < 64:
                st.warning("Not enough recent feature rows for a prediction.")
            else:
                prediction = model.predict(
                    f[model.feature_columns].tail(64).to_numpy()
                )
                st.subheader(t("model", lang))
                a, b, c, d = st.columns(4)
                a.metric("Signal", prediction["direction"])
                b.metric(t("confidence", lang), f'{prediction["confidence"]*100:.1f}%')
                c.metric(t("reliability", lang), f'{prediction["reliability"]*100:.1f}%')
                d.metric(t("expected", lang), f'{prediction["expected_return"]*100:+.2f}%')
                st.caption("Reliability is the validation-quality score blended with current model confidence; it is not a guarantee.")

def pct_value(value):
    return f"{float(value):+.2f}%" if value is not None else None
