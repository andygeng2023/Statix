from __future__ import annotations

import json
import gzip
import re
from pathlib import Path
from urllib.request import Request, urlopen

SEC_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,5}$")
VALID_EXCHANGES = {"Nasdaq", "NASDAQ", "NYSE", "NYSE American", "NYSE Arca"}


def _local_symbols(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        value.strip().upper()
        for value in path.read_text(encoding="utf-8").splitlines()
        if value.strip() and not value.startswith("#")
    ]


def _sec_symbols() -> list[str]:
    request = Request(
        SEC_URL,
        headers={
            "User-Agent": "Statix research dashboard contact@example.com",
            "Accept-Encoding": "gzip, deflate",
        },
    )
    with urlopen(request, timeout=30) as response:
        raw = response.read()
    try:
        raw = gzip.decompress(raw)
    except OSError:
        pass
    payload = json.loads(raw.decode("utf-8"))
    symbols = []
    for row in payload.get("data") or []:
        if len(row) < 4:
            continue
        symbol = str(row[2]).upper().strip()
        exchange = str(row[3] or "").strip()
        if exchange in VALID_EXCHANGES and SYMBOL_PATTERN.fullmatch(symbol):
            symbols.append(symbol)
    return symbols


def load_universe(path: Path, limit: int) -> list[str]:
    """Load local symbols and expand from SEC-listed exchange symbols."""
    symbols = []
    seen = set()
    for symbol in _local_symbols(path):
        if symbol not in seen:
            seen.add(symbol)
            symbols.append(symbol)

    if len(symbols) < limit:
        try:
            for symbol in _sec_symbols():
                if symbol not in seen:
                    seen.add(symbol)
                    symbols.append(symbol)
                if len(symbols) >= limit:
                    break
        except Exception:
            pass
    return symbols[:limit]
