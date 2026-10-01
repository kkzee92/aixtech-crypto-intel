"""Market data loading. Network access is injectable and off by default."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path

from crypto_intel.models import AssetClass, Candle

Fetcher = Callable[[str], dict]


def candle_from_mapping(row: dict) -> Candle:
    return Candle(
        symbol=str(row["symbol"]),
        asset_class=AssetClass(str(row["asset_class"])),
        timestamp=str(row["timestamp"]),
        open=float(row["open"]),
        high=float(row["high"]),
        low=float(row["low"]),
        close=float(row["close"]),
        volume=float(row["volume"]),
        funding_rate=float(row.get("funding_rate", 0.0)),
    )


def load_candles(path: str | Path) -> list[Candle]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("label") != "SYNTHETIC":
        raise ValueError("fixtures must be labelled SYNTHETIC")
    return [candle_from_mapping(row) for row in payload["candles"]]


def group_by_symbol(candles: Sequence[Candle]) -> dict[str, list[Candle]]:
    grouped: dict[str, list[Candle]] = {}
    for candle in candles:
        grouped.setdefault(candle.symbol, []).append(candle)
    for series in grouped.values():
        series.sort(key=lambda item: item.timestamp)
    return grouped


def parse_public_ticker(payload: dict) -> dict[str, float]:
    """Normalise a public ticker payload. Does not call the network."""
    price = payload.get("price")
    if price is None:
        raise ValueError("ticker payload missing price")
    return {
        "price": float(price),
        "volume": float(payload.get("volume", 0.0)),
    }


def fetch_public_ticker(symbol: str, fetcher: Fetcher) -> dict[str, float]:
    """Fetch through an injected callable so tests stay offline."""
    return parse_public_ticker(fetcher(symbol))
