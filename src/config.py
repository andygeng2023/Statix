from __future__ import annotations
import os
from pathlib import Path
import streamlit as st

APP_NAME="Statix"
MODEL_VERSION="statix-patchtemporal-v1"
FEATURE_VERSION="statix-features-v2"
HORIZON=5
SEQUENCE_LENGTH=64
ROOT=Path(__file__).resolve().parents[1]
ARTIFACT_DIR=ROOT/"artifacts"
MODEL_PATH=ARTIFACT_DIR/"statix_model.pt"
MODEL_META_PATH=ARTIFACT_DIR/"model_meta.json"
SCANNER_CACHE_TTL=300
QUOTE_TTL=20
HISTORY_TTL=300
MAX_SCAN=2000


def secret(name: str, default=None):
    try:
        value=st.secrets.get(name, default)
        return value
    except Exception:
        return os.getenv(name, default)


def database_url():
    return secret("database_url") or os.getenv("DATABASE_URL")


def require_auth():
    raw=secret("require_auth", False)
    if isinstance(raw, str):
        return raw.lower() in {"1","true","yes","on"}
    return bool(raw)
