"""Automated information desk for the paper-only crypto system.

Combines the class rule, the v0.5 overlay, cross-asset regime consensus, and
funding dispersion. The briefing digest covers the research output so a later
edit is visible. No network call and no order path.
"""

from __future__ import annotations

import hashlib
import json
from statistics import fmean

from crypto_intel.catalog import CATALOG_VERSION, parameter_digest
from crypto_intel.classification import injection_flags, schema_ok
from crypto_intel.models import Candle, Side
from crypto_intel.overlays import ENHANCEMENTS, apply_class_enhancement
from crypto_intel.regime import classify
from crypto_intel.strategies import signal_for


def _beta(series: list[Candle], benchmark: list[Candle]) -> float | None:
    length = min(len(series), len(benchmark))
    if length < 6:
        return None
    own = [series[-length + i].close / series[-length + i - 1].close - 1.0 for i in range(1, length)]
    bench = [benchmark[-length + i].close / benchmark[-length + i - 1].close - 1.0 for i in range(1, length)]
    variance = fmean(value * value for value in bench)
    if variance == 0:
        return None
    covariance = fmean(left * right for left, right in zip(own, bench))
    return round(covariance / variance, 4)


def funding_dispersion(grouped: dict[str, list[Candle]]) -> dict[str, float]:
    rates = [
        series[-1].funding_rate
        for series in grouped.values()
        if series and series[-1].asset_class.value == "perpetual"
    ]
    if not rates:
        return {"count": 0, "min": 0.0, "max": 0.0, "spread": 0.0}
    return {
        "count": len(rates),
        "min": min(rates),
        "max": max(rates),
        "spread": round(max(rates) - min(rates), 6),
    }


def regime_consensus(grouped: dict[str, list[Candle]]) -> dict[str, object]:
    labels = [classify(series).value for series in grouped.values() if series]
    counts = {name: labels.count(name) for name in ("trend", "range", "stress")}
    total = max(len(labels), 1)
    stress_fraction = counts["stress"] / total
    return {
        "counts": counts,
        "stress_fraction": round(stress_fraction, 4),
        "stand_aside": stress_fraction >= 0.5,
    }


def build_desk(
    grouped: dict[str, list[Candle]],
    *,
    fixture: dict | None = None,
) -> dict[str, object]:
    benchmark = grouped.get("ETH-USD")
    consensus = regime_consensus(grouped)
    rows = []
    for symbol, series in grouped.items():
        bench = None if symbol == "ETH-USD" else benchmark
        primary = signal_for(series, bench)
        enhanced = apply_class_enhancement(series, primary, bench)
        if consensus["stand_aside"] and enhanced.side in {Side.LONG, Side.SHORT}:
            enhanced = type(enhanced)(
                symbol=enhanced.symbol,
                asset_class=enhanced.asset_class,
                side=Side.FLAT,
                confidence=enhanced.confidence,
                reason=f"{enhanced.reason}; v0.5 book stress consensus",
                stop_distance_pct=enhanced.stop_distance_pct,
                size_fraction=0.0,
                horizon_bars=1,
            )
        rows.append(
            {
                "symbol": symbol,
                "asset_class": primary.asset_class.value,
                "regime": classify(series).value,
                "primary_side": primary.side.value,
                "side": enhanced.side.value,
                "size_fraction": enhanced.size_fraction,
                "confidence": enhanced.confidence,
                "enhancement": ENHANCEMENTS[primary.asset_class],
                "beta_to_eth": None if bench is None else _beta(series, bench),
                "reason": enhanced.reason,
            }
        )
    payload = fixture or {}
    note = str(payload.get("note", ""))
    report = {
        "version": CATALOG_VERSION,
        "parameter_digest": parameter_digest(),
        "paper_only": True,
        "live_enabled": False,
        "schema_ok": schema_ok(payload) if payload else True,
        "injection_flags": injection_flags(note),
        "regime_consensus": consensus,
        "funding_dispersion": funding_dispersion(grouped),
        "rows": rows,
    }
    material = json.dumps(report, sort_keys=True)
    report["briefing_digest"] = hashlib.sha256(material.encode()).hexdigest()
    return report
