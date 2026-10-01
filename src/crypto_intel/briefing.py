"""Information briefing across asset classes. Paper research only."""

from __future__ import annotations

from crypto_intel.costs import COST_BPS
from crypto_intel.engine import run_once
from crypto_intel.models import Candle
from crypto_intel.regime import classify
from crypto_intel.security import AuditLog
from crypto_intel.strategies import PLAYBOOK


def build_brief(
    grouped: dict[str, list[Candle]],
    *,
    audit: AuditLog | None = None,
) -> dict[str, object]:
    log = audit or AuditLog()
    benchmark = grouped.get("ETH-USD")
    rows = []
    for symbol, series in grouped.items():
        signal, fill = run_once(
            series,
            audit=log,
            benchmark=benchmark if symbol != "ETH-USD" else None,
        )
        rows.append(
            {
                "symbol": symbol,
                "asset_class": signal.asset_class.value,
                "regime": classify(series).value,
                "side": fill.side.value,
                "size_fraction": fill.size_fraction,
                "confidence": signal.confidence,
                "horizon_bars": signal.horizon_bars,
                "cost_bps": COST_BPS[signal.asset_class],
                "hypothesis": PLAYBOOK[signal.asset_class]["hypothesis"],
                "reason": fill.reason,
                "mode": fill.mode.value,
            }
        )
    alerts = [row for row in rows if row["side"] == "alert"]
    return {
        "mode": "paper",
        "symbols": len(rows),
        "alerts": len(alerts),
        "audit_ok": log.verify(),
        "audit_events": len(log.events),
        "rows": rows,
    }
