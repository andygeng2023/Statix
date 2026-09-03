# Statix

Statix is a machine-learning stock analysis application built with Python,
Streamlit and PyTorch.

## Architecture

The application separates:

1. Market data
2. Feature generation
3. Model training
4. Model inference
5. Stock scanning
6. User storage
7. UI

The model is trained offline and loaded once for inference.

## Model

Statix uses a PatchTST-style temporal architecture.

Inputs:

- historical returns
- momentum
- moving-average relationships
- volatility
- RSI
- ATR
- MACD
- Bollinger position
- volume
- intraday range
- gaps

Outputs:

- 1-day expected return
- 5-day expected return
- 20-day expected return
- five-class directional probability

Classes:

- Strong Bearish
- Bearish
- Neutral
- Bullish
- Strong Bullish

## Training

Build the dataset:

```bash
python training/build_dataset.py
```

Train:

```bash
python training/train.py
```

The resulting model is saved to:

```bash
artifacts/statix_model.pt
```
