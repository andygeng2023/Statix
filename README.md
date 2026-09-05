# Statix

Statix is a Streamlit stock-research dashboard for market context, historical price analysis, watchlists, calibrated model signals, and ranked scanner suggestions.

## Version

Current model format: `statix-walkforward-calibrated-v4`

This version includes:

- Point-in-time technical, volatility, volume, market, sector, and beta features
- Relative-return targets against market and sector context
- 1-day, 5-day, and 20-day training targets, with the 5-day target as the primary signal
- Chronological train, calibration, and test windows
- XGBoost plus HistGradientBoosting classification/regression
- Sigmoid probability calibration on a later validation period
- Held-out accuracy, precision, recall, F1, ROC-AUC, Brier score, RMSE, return, and baseline metrics
- A Kalman and correlation-graph scanner prefilter

The detail screen displays 1D, 5D, 10D, 1M, 6M, 1Y, 5Y, 10Y, and 20Y model-derived projections with uncertainty ranges. Longer horizons are projections of the trained 5-day signal, not independently trained forecasts.

## Running Locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m compileall -q app.py src training
streamlit run app.py
```
## On Streamlit Cloud

Open
```bash
ageng-statix.streamlit.app
```
in your browser.
You can add the website to your home screen by pressing 'Share' > 'Add to home screen' on safari.

## Compatibility

This application is mainly designed for horizontal-screen devices such as tablets and computers. Phones are supported, but UI formatting may not be as intricate.

## Tabs

- **Home**: market pulse, watchlist context, featured symbols, and recent scanner results
- **Stocks**: search, watchlist, historical charts, pan/zoom interaction, and model projections
- **Discover**: scanner controls, progress, ranked suggestions, and sector groupings
- **Settings**: language and data-provider preferences

## Authentication

Google OAUTH is enabled. 

PLease sign in with your google account before using so that data can be saved to your account.

## Providers

Real-time data is provided by AkShare, QuantDash and yfinance. 
Quantdash free daily limits apply.
'Automatic fallback' is recommended. Streamlit automatically goes through AkShare, QuantDash and yfinance for information.

## License

See [LICENSE](LICENSE).

## Final Note

> Research software only. Predictions are estimates, not financial advice or guarantees.

Enjoy!