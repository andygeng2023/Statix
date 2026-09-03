import hashlib
import json

import streamlit as st

from src.config import SETTINGS
from src.data.market import get_stock_data
from src.data.provider import get_provider
from src.models.ensemble import (
    train_global_model,
)
from src.models.features import (
    create_features,
)
from src.scanner.engine import (
    scan_universe,
)
from src.storage.database import (
    get_scan,
    save_scan,
)


st.title(
    "Market Scanner"
)

st.caption(
    "Research ranking tool. Results are "
    "experimental model outputs."
)


provider = get_provider()


st.write(
    f"Data provider: **{provider.name}**"
)


st.subheader(
    "Scanner Controls"
)


limit = st.slider(
    "Results",
    min_value=5,
    max_value=100,
    value=SETTINGS.scanner_default_limit,
)


workers = st.slider(
    "Parallel workers",
    min_value=2,
    max_value=32,
    value=8,
)


universe_text = st.text_area(
    "Universe",
    value=(
        "AAPL,MSFT,NVDA,AMZN,GOOGL,META,"
        "TSLA,AVGO,AMD,NFLX,JPM,V,MA,"
        "COST,WMT,LLY,UNH,ORCL,CRM"
    ),
    help=(
        "For production, load a maintained "
        "2,000–10,000 symbol universe from "
        "your market-data service."
    ),
)


tickers = [
    ticker.strip().upper()
    for ticker in universe_text.split(",")
    if ticker.strip()
]


if len(tickers) > SETTINGS.scanner_max_symbols:

    st.error(
        f"Maximum universe is "
        f"{SETTINGS.scanner_max_symbols}."
    )

    st.stop()


st.write(
    f"Universe: **{len(tickers)} symbols**"
)


if st.button(
    "Run Scanner",
    type="primary",
    use_container_width=True,
):

    if not tickers:

        st.warning(
            "Enter at least one symbol."
        )

        st.stop()

    with st.status(
        "Preparing scanner...",
        expanded=True,
    ) as status:

        st.write(
            "Loading market context..."
        )

        market = get_stock_data(
            "SPY",
            "2y",
            "1d",
        )

        if market.empty:

            status.update(
                label="Market context unavailable",
                state="error",
            )

            st.stop()

        st.write(
            "Building global model..."
        )

        seed_ticker = tickers[0]

        seed_history = get_stock_data(
            seed_ticker,
            "2y",
            "1d",
        )

        training, _, features = (
            create_features(
                seed_history,
                market,
                SETTINGS.prediction_horizon,
            )
        )

        model = train_global_model(
            training,
            tuple(features),
        )

        st.write(
            "Scoring universe..."
        )

        results = scan_universe(
            tickers=tickers,
            model=model,
            market_df=market,
            max_workers=workers,
            limit=limit,
        )

        scan_key = hashlib.sha256(
            json.dumps(
                sorted(tickers)
            ).encode()
        ).hexdigest()

        save_scan(
            scan_key,
            results,
        )

        st.session_state[
            "scan_results"
        ] = results

        status.update(
            label=(
                f"Completed · "
                f"{len(results)} results"
            ),
            state="complete",
        )


results = st.session_state.get(
    "scan_results",
    [],
)


if not results:

    st.info(
        "Run a scan to see ranked results."
    )

    st.stop()


st.subheader(
    "Top Statix Results"
)


header = st.columns(
    [1, 1.4, 1.5, 1.2, 1.2, 1]
)

header[0].write("Ticker")
header[1].write("Price")
header[2].write("Signal")
header[3].write("Probability")
header[4].write("Reliability")
header[5].write("Open")


for index, result in enumerate(
    results
):

    columns = st.columns(
        [1, 1.4, 1.5, 1.2, 1.2, 1]
    )

    columns[0].write(
        f"**{result['ticker']}**"
    )

    columns[1].write(
        f"${result['price']:,.2f}"
    )

    columns[2].write(
        result["signal"]
    )

    columns[3].write(
        f"{result['probability'] * 100:.0f}%"
    )

    columns[4].write(
        f"{result['reliability'] * 100:.0f}%"
    )

    if columns[5].button(
        "Open",
        key=f"scanner_open_{index}",
    ):

        st.session_state[
            "selected_ticker"
        ] = result["ticker"]

        st.switch_page(
            "pages/stock.py"
        )