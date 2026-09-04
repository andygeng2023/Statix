# Statix Production 2.0

## Architecture
- One Streamlit app with exactly four top-level tabs: Home, Stocks, Discover, Settings.
- Stocks contains search + persistent user watchlist cards + stock detail.
- Discover contains the persistent scanner queue and recommendation cards.
- Settings controls language, provider preference, and identity display.
- Market data fallback: AKShare -> QuantDash (if configured) -> TuShare -> yfinance.
- SEC is used for U.S. security discovery/metadata fallback; it is not a live price feed.
- Scanner worker runs as a separate always-on process and uses PostgreSQL as a durable queue.

## Python
Use Python 3.14. Current Streamlit documentation supports Python 3.10-3.14, and current Streamlit releases include Python 3.14 support.

## Install
```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Windows activation: `.venv\Scripts\activate`

## Local secrets
Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`. Never commit the real file.

## Train
```bash
python -m training.train
```
This creates `artifacts/statix_model.joblib`. The model is a fast global tabular time-series ensemble, deliberately chosen over a heavyweight neural network for low-latency inference and easier Python 3.14 deployment.

## Run app
```bash
streamlit run app.py
```

## Run worker
```bash
python scanner_worker.py
```
Run the worker on a persistent service, not inside Streamlit Community Cloud.

## Production database
Use managed PostgreSQL and put the connection string in Streamlit Secrets and the worker's environment.

## QuantDash
This release includes a generic QuantDash HTTP adapter, but I could not verify a public official QuantDash API contract from authoritative documentation. Configure its base URL, API key, and paths from the actual QuantDash service/account you use; do not assume the placeholder endpoints are universal.

## Data provider notes
yfinance is intended by its maintainers for research/personal use, so obtain appropriately licensed data before commercial/public deployment.
