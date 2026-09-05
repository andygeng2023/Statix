# Statix

Statix is a Streamlit stock-research dashboard with four top-level areas: Home, Stocks, Discover, and Settings.

## Provider architecture

Automatic order:

1. QuantDash
2. AKShare
3. yfinance

TuShare has been removed.

QuantDash uses its official Python SDK and API key. It does not require a manually configured base URL or endpoint paths.

## Important model change

The previous model used five noisy daily-return classes and had an inference mismatch: training averaged each 64-day sequence, while inference sent all 64 rows to the classifier and read only the first result.

This version:

- uses three classes: Bearish / Neutral / Bullish
- uses the same 64-day sequence aggregation during training and inference
- trains on 10 years of daily data
- automatically expands the starter universe to the current S&P 500 when the local universe has fewer than 100 symbols
- downloads training data in Yahoo Finance batches
- uses an XGBoost tabular branch plus an LSTM sequence branch when the optional
	training dependencies are installed
- refuses to load the old incompatible model artifact

Reliability is a model-quality score derived from validation accuracy and current confidence. It is not a probability that a prediction will be profitable.

## Local setup

Python 3.14 is supported.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m compileall -q .
```

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in your API key/database settings.

Run:

```bash
streamlit run app.py
```

## Train the model

The training script automatically expands the tiny starter universe to the S&P 500 list.

Default:

- 500 symbols maximum
- 10 years of daily Yahoo Finance history
- 64-day sequence
- 5-day prediction horizon
- detailed predictions blend XGBoost and LSTM outputs

Run:

```bash
python -m training.train
```

Install the model dependencies before retraining:

```bash
pip install -r requirements.txt
```

For roughly 2,000 stocks, set the training limit and expect a long download and
training run:

```bash
STATIX_TRAIN_MAX_SYMBOLS=2000 STATIX_TRAIN_PERIOD=10y python -m training.train
```

The generated artifact contains the XGBoost branch. An LSTM branch is optional
and is added only when a compatible PyTorch build is installed separately. If
PyTorch cannot load, training still completes with XGBoost and reports that the
optional LSTM branch was skipped. The application loads only this v3 artifact.

To change the training size:

```bash
STATIX_TRAIN_MAX_SYMBOLS=500 python -m training.train
```

To use another period supported by Yahoo Finance:

```bash
STATIX_TRAIN_PERIOD=10y python -m training.train
```

The output is:

```text
artifacts/statix_model.joblib
artifacts/model_meta.json
```

Commit both:

```bash
git add artifacts/statix_model.joblib artifacts/model_meta.json
git commit -m "Add Statix v3 model"
git push
```

Streamlit Community Cloud will redeploy from GitHub.

## Why the old 31.44% reliability does not carry over

The old artifact was trained on only about 40 symbols and used five classes. A five-class classifier has a much harder validation problem than a three-class classifier. More importantly, its sequence representation was inconsistent between training and inference.

Do not edit the reliability number manually. Retrain the v3 model and inspect the reported validation accuracy, validation RMSE, training windows, validation windows, and usable symbol count.

## Discover scanner

Each scan now applies a fast one-dimensional Kalman filter, propagates recent
returns through a correlation graph, keeps the best 100 candidates, and sends
those candidates through the stronger model. The UI displays the final 20
suggestions. These are ranked signals, not financial advice.

The scan now runs directly when the user clicks `Run scanner` in the Streamlit
app. It does not require PostgreSQL, a queue, or a separate worker host. Results
are kept in the current Streamlit session and are not a permanent shared cache.
The app offers up to 500 symbols because a 2,000-symbol network scan is too
long for a normal Streamlit request; use 2,000 symbols for offline training.

Validate the app with:

```bash
python -m compileall -q app.py src training
python -m training.train
```

## Google sign-in

Set `require_auth = true` and configure the `[auth]` section in Streamlit secrets with your OIDC provider. For Google, the redirect URI must match:

```text
https://YOUR-APP-NAME.streamlit.app/oauth2callback
```

Keep API keys, OAuth secrets, and database passwords out of Git.
