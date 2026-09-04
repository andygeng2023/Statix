from __future__ import annotations

import streamlit as st

from src.storage.database import enqueue_scan, job_status, latest_scan, get_settings
from src.ui.components import card_row, t
from src.data.market import history, quote
from src.data.search import security_name

settings = get_settings()
lang = st.session_state.get("language_preference", settings.get("language", "en"))

st.markdown(f"# {t('discover', lang)}")
st.caption(t("scanner_caption", lang))

job, rows = latest_scan()
status = job_status()
limit = st.select_slider(t("universe_size", lang), options=[100, 250, 500, 1000, 1500, 2000], value=500)

if not job and (not status or status.status not in {"queued", "running"}):
    enqueue_scan(limit)

if st.button(t("queue", lang), type="primary"):
    jid = enqueue_scan(limit)
    if jid:
        st.success(f"{t('scan_job', lang)} #{jid}")
    else:
        st.error(t("storage_unavailable", lang))

if status:
    st.caption(f"{t('job_status', lang)} #{status.id}: {status.status}")

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

if job and rows:
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
