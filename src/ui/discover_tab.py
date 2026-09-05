from __future__ import annotations

import streamlit as st

from src.models.scanner_service import scan
from src.storage.database import get_settings
from src.ui.components import card_row, t
from src.data.market import history, quote
from src.data.search import security_name

settings = get_settings()
lang = st.session_state.get("language_preference", settings.get("language", "en"))

st.markdown(f"# {t('discover', lang)}")
st.caption(t("scanner_caption", lang))

limit = st.select_slider(t("universe_size", lang), options=[100, 250, 500], value=500)

rows = st.session_state.get("latest_scan_rows", [])

if st.button(t("queue", lang), type="primary"):
    with st.spinner("Scanning market data..."):
        try:
            rows = scan(limit)
            st.session_state["latest_scan_rows"] = rows
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

area_symbols = {
    "Top stocks": ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "META", "AVGO", "TSLA"],
    "Technology": ["NVDA", "MSFT", "AAPL", "AVGO", "ORCL", "AMD", "CRM", "ADBE"],
    "Healthcare": ["LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ISRG", "PFE"],
    "Financials": ["JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "BLK"],
    "Consumer": ["AMZN", "WMT", "COST", "HD", "MCD", "NKE", "SBUX", "TJX"],
    "ETFs": ["SPY", "QQQ", "DIA", "IWM", "XLK", "XLF", "XLE", "ARKK"],
}
area_labels = {
    "Top stocks": t("area_top_stocks", lang),
    "Technology": t("area_technology", lang),
    "Healthcare": t("area_healthcare", lang),
    "Financials": t("area_financials", lang),
    "Consumer": t("area_consumer", lang),
    "ETFs": t("area_etfs", lang),
}

st.subheader(t("top_by_area", lang))
selected_area = st.selectbox(t("area", lang), list(area_symbols), format_func=lambda value: area_labels[value], label_visibility="collapsed")
area_items = []
for ticker in area_symbols[selected_area]:
    q = quote(ticker)
    area_items.append(
        {
            "ticker": ticker,
            "name": security_name(ticker),
            "price": q.get("price"),
            "change_pct": q.get("change_pct"),
            "df": history(ticker, "3mo"),
        }
    )
card_row(area_items, key_prefix="discover_area")

if rows:
    st.subheader(t("latest", lang))
    items = []
    for row in rows[:16]:
        ticker = row["ticker"]
        q = quote(ticker)
        df = history(ticker, "6mo")
        items.append({
            "ticker": ticker,
            "name": security_name(ticker),
            "price": q.get("price", row.get("price")),
            "change_pct": q.get("change_pct", row.get("change_pct")),
            "df": df,
            "signal": row.get("signal"),
            "confidence": row.get("confidence"),
            "reliability": row.get("reliability"),
            "expected_return": row.get("expected_return"),
        })
    card_row(
        items,
        key_prefix="discover",
    )

    bullish = [row for row in rows if str(row.get("signal", "")).lower() == "bullish"]
    if bullish:
        st.subheader(t("bullish_signals", lang))
        card_row(
            [
                {
                    "ticker": row["ticker"],
                    "name": security_name(row["ticker"]),
                    "price": quote(row["ticker"]).get("price", row.get("price")),
                    "change_pct": quote(row["ticker"]).get("change_pct", row.get("change_pct")),
                    "df": history(row["ticker"], "6mo"),
                    "signal": row.get("signal"),
                    "confidence": row.get("confidence"),
                    "reliability": row.get("reliability"),
                    "expected_return": row.get("expected_return"),
                }
                for row in bullish[:12]
            ],
            key_prefix="discover_bullish",
        )
else:
    st.info(t("no_scan", lang))
