"""Automated cryptocurrency information pipeline. Paper only.

Stages describe how a research run is assembled. This module does not poll an
exchange, open a socket, or place an order. An external scheduler may call the
CLI; the package itself stays offline by default.
"""

from __future__ import annotations

from crypto_intel.models import AssetClass

PIPELINE_VERSION = "0.7.0"

STAGES: tuple[str, ...] = (
    "ingest",
    "attest",
    "quality",
    "class_strategy",
    "risk_gate",
    "cross_overlay",
    "class_enhance",
    "sleeve",
    "brief",
    "audit",
)

# Information freshness budgets. A stale series is a research halt, not a trade.
FRESHNESS_SLA_SECONDS: dict[str, int] = {
    AssetClass.MAJOR.value: 60,
    AssetClass.LARGE_CAP_ALT.value: 120,
    AssetClass.STABLECOIN.value: 30,
    AssetClass.DEFI.value: 180,
    AssetClass.MEME.value: 60,
    AssetClass.L2.value: 120,
    AssetClass.RWA.value: 900,
    AssetClass.PERPETUAL.value: 30,
}


def pipeline_manifest() -> dict[str, object]:
    """Declared automation. Cadence is documentation, not a running poller."""
    return {
        "version": PIPELINE_VERSION,
        "live_enabled": False,
        "network_default": False,
        "order_path": False,
        "stages": list(STAGES),
        "cadence": "external scheduler may invoke scan; this package does not poll exchanges",
        "freshness_sla_seconds": dict(FRESHNESS_SLA_SECONDS),
    }


def evaluate_freshness(asset_class: str, age_seconds: int) -> dict[str, object]:
    """Refuse a series that is older than its class information SLA."""
    if age_seconds < 0:
        raise ValueError("age_seconds cannot be negative")
    if asset_class not in FRESHNESS_SLA_SECONDS:
        raise ValueError(f"unknown asset class {asset_class}")
    sla = FRESHNESS_SLA_SECONDS[asset_class]
    return {
        "asset_class": asset_class,
        "age_seconds": age_seconds,
        "sla_seconds": sla,
        "ok": age_seconds <= sla,
        "live_enabled": False,
    }


def assemble_packet(
    *,
    label: str,
    stage_notes: dict[str, str],
    freshness_ok: bool,
) -> dict[str, object]:
    """Bind a research run. A failed freshness check zeroes the paper book."""
    if label not in {"SYNTHETIC", "PUBLIC_READ"}:
        raise ValueError("information packet requires a research label")
    missing = [stage for stage in STAGES if stage not in stage_notes]
    if missing:
        raise ValueError(f"information packet missing stages: {', '.join(missing)}")
    return {
        "version": PIPELINE_VERSION,
        "label": label,
        "stages": stage_notes,
        "freshness_ok": freshness_ok,
        "paper_size_scale": 1.0 if freshness_ok else 0.0,
        "live_enabled": False,
        "order_path": False,
    }
