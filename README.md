# Statix

Statix is a Streamlit stock-research dashboard for market context, historical price analysis, watchlists, calibrated model signals, and ranked scanner suggestions.

> Research software only. Predictions are estimates, not financial advice or guarantees.

## Version

Current model format: `statix-walkforward-calibrated-v4`

The v4 pipeline uses:

- Point-in-time technical, volatility, volume, market, sector, and beta features
- Relative-return targets against market and sector context
- 1-day, 5-day, and 20-day training targets, with the 5-day target as the primary signal
- Chronological train, calibration, and test windows
- XGBoost plus HistGradientBoosting classification/regression
- Sigmoid probability calibration on a later validation period
- Held-out accuracy, precision, recall, F1, ROC-AUC, Brier score, RMSE, return, and baseline metrics
- A Kalman and correlation-graph scanner prefilter

The detail screen displays 1D, 5D, 10D, 1M, 6M, 1Y, 5Y, 10Y, and 20Y model-derived projections with uncertainty ranges. Longer horizons are projections of the trained 5-day signal, not independently trained forecasts.

## Run Locally

Python 3.14 is supported.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m compileall -q app.py src training
streamlit run app.py
```

The app uses automatic provider fallback in this order:

1. QuantDash, when configured
2. AKShare
3. yfinance

Configure secrets in `.streamlit/secrets.toml`. Never commit API keys, OAuth secrets, database passwords, or private credentials.

## Train A Model

Training downloads daily OHLCV history, market context, sector ETF context, calculates point-in-time features, performs chronological validation, calibrates probabilities, evaluates the held-out period, and writes:

```text
artifacts/statix_model.joblib
artifacts/model_meta.json
```

Recommended 2,000-symbol run:

```bash
source .venv/bin/activate
STATIX_TRAIN_MAX_SYMBOLS=2000 \
STATIX_TRAIN_PERIOD=10y \
python -m training.train
```

The default path stores compact feature-window means and does not require PyTorch. The optional LSTM branch is only attempted when explicitly enabled and a compatible PyTorch installation is available:

```bash
STATIX_ENABLE_LSTM=1 \
STATIX_TRAIN_MAX_SYMBOLS=2000 \
STATIX_TRAIN_PERIOD=10y \
python -m training.train
```

Useful controls:

```bash
STATIX_MAX_WINDOWS_PER_SYMBOL=80 python -m training.train
STATIX_TRAIN_MAX_SYMBOLS=500 python -m training.train
STATIX_TRAIN_PERIOD=5y python -m training.train
```

`training/universe.txt` is a seed list. The runtime universe loader expands it with current SEC-listed NYSE/Nasdaq symbols up to the requested limit, capped at 2,000.

After training:

```bash
git add artifacts/statix_model.joblib artifacts/model_meta.json
git commit -m "Train Statix v4 model"
git push
```

Streamlit Community Cloud loads the committed artifact from `artifacts/` after redeployment. If the artifact version does not match the application, predictions are disabled instead of silently using an incompatible model.

## Scanner

The Discover scanner runs in the Streamlit process and does not require a worker host or queue. It:

1. Loads the selected universe with concurrent market-history requests
2. Applies a fast Kalman momentum filter
3. Propagates recent returns through a correlation graph
4. Keeps roughly 100 candidates
5. Scores them with the trained model and risk-aware ranking
6. Displays the top 20 suggestions

The scanner includes a live progress bar. Results are kept in the current Streamlit session. A 500-symbol scan is the practical interactive limit; use the 2,000-symbol setting for offline training.

## App Areas

- **Home**: market pulse, watchlist context, featured symbols, and recent scanner results
- **Stocks**: search, watchlist, historical charts, pan/zoom interaction, and model projections
- **Discover**: scanner controls, progress, ranked suggestions, and sector groupings
- **Settings**: language and data-provider preferences

Cards use same-tab links to the Stocks detail view. Charts support hover, pan, zoom, and selectable history ranges without box selection.

## Validation

```bash
source .venv/bin/activate
python -m compileall -q app.py src training
git diff --check
```

## Authentication

Set `require_auth = true` in Streamlit secrets and configure the Streamlit OIDC `[auth]` section. For Google sign-in, the redirect URI must match:

```text
https://YOUR-APP-NAME.streamlit.app/oauth2callback
```

## License

See [LICENSE](LICENSE).
