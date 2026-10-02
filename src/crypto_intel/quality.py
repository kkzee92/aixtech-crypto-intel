"""Candle-series quality gate for the information system.

Flags windows that are too short, stale, duplicated, or gapped. This does not
fetch data and does not place orders.
"""

from __future__ import annotations

from dataclasses import dataclass

from crypto_intel.models import Candle


@dataclass(frozen=True)
class QualityReport:
    ok: bool
    score: float
    issues: tuple[str, ...]


def assess(candles: list[Candle]) -> QualityReport:
    issues: list[str] = []
    if len(candles) < 8:
        issues.append("short_history")
    if any(candle.volume == 0 for candle in candles[-8:]):
        issues.append("zero_volume")
    timestamps = [candle.timestamp for candle in candles]
    if len(timestamps) != len(set(timestamps)):
        issues.append("duplicate_timestamp")
    if timestamps != sorted(timestamps):
        issues.append("unsorted_timestamps")
    closes = [candle.close for candle in candles]
    for index in range(1, len(closes)):
        previous = closes[index - 1]
        if previous <= 0 or closes[index] <= 0:
            issues.append("non_positive_price")
            break
        if abs(closes[index] / previous - 1.0) > 0.40:
            issues.append("jump_over_40pct")
            break
    unique = tuple(dict.fromkeys(issues))
    score = round(max(0.0, 1.0 - 0.2 * len(unique)), 4)
    return QualityReport(ok=not unique, score=score, issues=unique)
