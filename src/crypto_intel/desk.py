"""Version 0.8 information desk. Paper only.

Assembles a research dossier from an already-loaded fixture. It does not poll
an exchange, open a socket, or place an order. A failed zone or freshness
check scales the paper book to zero.
"""

from __future__ import annotations

from crypto_intel.automation import FRESHNESS_SLA_SECONDS, evaluate_freshness
from crypto_intel.models import AssetClass, Candle

DESK_VERSION = "0.8.0"

DESK_STAGES: tuple[str, ...] = (
    "ingest",
    "attest",
    "zone_check",
    "quality",
    "class_strategy",
    "risk_gate",
    "cross_overlay",
    "class_enhance",
    "sleeve",
    "class_overlay",
    "dossier",
    "audit",
)

CORRELATION_SHOCK_DROP = 0.04
CORRELATION_SHOCK_COUNT = 3


def desk_manifest() -> dict[str, object]:
    """Declared information desk. Cadence is external; this package stays offline."""
    return {
        "version": DESK_VERSION,
        "live_enabled": False,
        "network_default": False,
        "order_path": False,
        "stages": list(DESK_STAGES),
        "cadence": "external scheduler may invoke desk; this package does not poll exchanges",
        "freshness_sla_seconds": dict(FRESHNESS_SLA_SECONDS),
        "correlation_shock": {
            "lookback_bars": 3,
            "drop": CORRELATION_SHOCK_DROP,
            "count": CORRELATION_SHOCK_COUNT,
            "effect": "scale paper book to 0.5; does not place an order",
        },
    }


def correlation_shock(grouped: dict[str, list[Candle]]) -> dict[str, object]:
    """Count non-stable series that fell at least 4 percent over three bars."""
    stressed: list[str] = []
    for symbol, series in grouped.items():
        if len(series) < 4:
            continue
        if series[-1].asset_class is AssetClass.STABLECOIN:
            continue
        move = series[-1].close / series[-4].close - 1.0
        if move <= -CORRELATION_SHOCK_DROP:
            stressed.append(symbol)
    active = len(stressed) >= CORRELATION_SHOCK_COUNT
    return {
        "active": active,
        "symbols": stressed,
        "paper_size_scale": 0.5 if active else 1.0,
        "live_enabled": False,
        "order_path": False,
    }


def build_dossier(
    grouped: dict[str, list[Candle]],
    *,
    label: str,
    ages: dict[str, int],
    zone_ok: bool,
) -> dict[str, object]:
    """Bind a research dossier. Stale or unzoned input zeroes paper size."""
    if label not in {"SYNTHETIC", "PUBLIC_READ"}:
        raise ValueError("information dossier requires a research label")
    if not grouped:
        raise ValueError("information dossier requires at least one series")
    freshness = []
    freshness_ok = True
    for symbol, series in grouped.items():
        asset_class = series[-1].asset_class.value
        age = ages.get(symbol, 0)
        row = evaluate_freshness(asset_class, age)
        row["symbol"] = symbol
        freshness.append(row)
        freshness_ok = freshness_ok and bool(row["ok"])
    shock = correlation_shock(grouped)
    scale = 1.0
    if not freshness_ok or not zone_ok:
        scale = 0.0
    elif shock["active"]:
        scale = 0.5
    return {
        "version": DESK_VERSION,
        "label": label,
        "symbols": sorted(grouped),
        "freshness": freshness,
        "freshness_ok": freshness_ok,
        "zone_ok": zone_ok,
        "correlation_shock": shock,
        "paper_size_scale": scale,
        "live_enabled": False,
        "order_path": False,
    }
