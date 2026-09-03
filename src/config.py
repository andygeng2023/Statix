import os
from pathlib import Path

APP_NAME = "Statix"

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "artifacts"
MODEL_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODEL_DIR / "statix_model.pt"

MODEL_VERSION = "statix-v11-patchtst-1"
FEATURE_VERSION = "statix-v11-features-1"

LOOKBACK = 64
PREDICTION_HORIZONS = [1, 5, 20]

QUOTE_CACHE_SECONDS = 15
HISTORY_CACHE_SECONDS = 300

MAX_SCANNER_UNIVERSE = 10_000

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("database_url")
    or "sqlite:///statix.db"
)