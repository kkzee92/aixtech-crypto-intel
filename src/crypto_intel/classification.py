"""Fixture schema and note-injection checks for the research information path.

Defensive only. This module does not fetch data and does not place orders.
"""

from __future__ import annotations

ALLOWED_FIXTURE_KEYS = frozenset({"label", "note", "candles"})
ALLOWED_CANDLE_KEYS = frozenset(
    {
        "symbol",
        "asset_class",
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "funding_rate",
    }
)
REQUIRED_CANDLE_KEYS = frozenset({"symbol", "asset_class", "timestamp", "open", "high", "low", "close", "volume"})
ALLOWED_LABELS = frozenset({"SYNTHETIC", "PUBLIC_READ"})
INJECTION_MARKERS = (
    "ignore previous",
    "ignore all instructions",
    "system prompt",
    "exfiltrate",
    "api_key=",
    "begin private key",
)


def unexpected_keys(payload: dict) -> list[str]:
    extra = sorted(set(payload) - ALLOWED_FIXTURE_KEYS)
    candles = payload.get("candles")
    if isinstance(candles, list):
        for candle in candles:
            if isinstance(candle, dict):
                extra.extend(sorted(set(candle) - ALLOWED_CANDLE_KEYS))
    return sorted(set(extra))


def schema_ok(payload: dict) -> bool:
    if payload.get("label") not in ALLOWED_LABELS:
        return False
    candles = payload.get("candles")
    if not isinstance(candles, list) or not candles:
        return False
    if unexpected_keys(payload):
        return False
    return all(isinstance(candle, dict) and REQUIRED_CANDLE_KEYS <= set(candle) for candle in candles)


def injection_flags(text: str) -> list[str]:
    lowered = text.lower()
    return [marker for marker in INJECTION_MARKERS if marker in lowered]
