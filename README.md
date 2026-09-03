# Statix

Statix is an experimental stock-market prediction and research platform built with Python and Streamlit.

## Features

- Stock search
- Stock detail pages
- Historical charts
- Watchlists
- Multi-user storage
- OIDC authentication
- Machine-learning predictions
- Five-class prediction system
- Model probability distribution
- Reliability scoring
- Model agreement
- Validation accuracy
- Market-context features
- Market scanner
- Cached market data
- Cached model resources
- PostgreSQL support
- SQLite local development

## Architecture

Statix separates:

1. Market data
2. Feature engineering
3. Model training
4. Model inference
5. Reliability scoring
6. User storage
7. Scanner ranking
8. UI

The expensive model-training path is separated from normal prediction inference.

## Local setup

Create a virtual environment:

```bash
python -m venv .venv