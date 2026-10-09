"""v0.22 liquidity and counterparty guards, plus a cyber kill-chain plane.

Eighteenth pass. Guards can only shrink paper size. The liquidity desk is an
offline information artifact. The kill-chain plane maps adversary stages to
controls. It never stores key material and never opens an execution zone.
"""

from __future__ import annotations

import hashlib
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side

LIQUIDITY_NOTES = {
    AssetClass.MAJOR.value: "thin-book haircut when volume is below 40 percent of median and range exceeds 1.5 percent",
    AssetClass.LARGE_CAP_ALT.value: "venue-chop haircut when range exceeds 5 percent and close stays inside 1 percent",
    AssetClass.STABLECOIN.value: "redemption-stress watch when range exceeds 25 bp and close is 10 bp off the peg",
    AssetClass.DEFI.value: "cascade veto when three bars each lose more than 1.5 percent",
    AssetClass.MEME.value: "liquidity-vacuum veto when a 10 percent burst meets volume below 30 percent of median",
    AssetClass.L2.value: "sequencer-stall haircut when four volumes match and price is flat",
    AssetClass.RWA.value: "nav-dislocation haircut when the close is more than 3 percent from the eight-bar mean",
    AssetClass.PERPETUAL.value: "funding-acceleration veto when the funding change is at least 8 bp",
}

STRESS_BUDGET = {
    AssetClass.MAJOR.value: 0.08,
    AssetClass.LARGE_CAP_ALT.value: 0.04,
    AssetClass.STABLECOIN.value: 0.0,
    AssetClass.DEFI.value: 0.02,
    AssetClass.MEME.value: 0.005,
    AssetClass.L2.value: 0.03,
    AssetClass.RWA.value: 0.02,
    AssetClass.PERPETUAL.value: 0.02,
}

KILL_CHAIN = (
    {
        "stage": "reconnaissance",
        "control": "public research tree only; no secret or wallet fixtures",
        "detect": "gitleaks and PDPA tripwire",
    },
    {
        "stage": "initial_access",
        "control": "pasted trade, withdrawal, seed, and private-key scopes are refused",
        "detect": "refuse_trade_secret and redaction",
    },
    {
        "stage": "execution",
        "control": "fixtures must be labelled SYNTHETIC or PUBLIC_READ",
        "detect": "source attestation digest",
    },
    {
        "stage": "persistence",
        "control": "audit events are hash-chained",
        "detect": "chain verification failure",
    },
    {
        "stage": "privilege_escalation",
        "control": "no role can place an order or enable live trading",
        "detect": "RBAC deny on place_order and enable_live",
    },
    {
        "stage": "exfiltration",
        "control": "secret, wallet, and personal strings are blocked before egress",
        "detect": "DLP screen",
    },
    {
        "stage": "impact",
        "control": "there is no order router and no execution zone",
        "detect": "paper-only mode guard",
    },
)

REFUSED_ACTIONS = ("place_order", "withdraw", "enable_live", "export_secret", "load_trade_key")


def apply_v22(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Eighteenth-pass liquidity guard. Size cannot increase."""
    if len(candles) < 8:
        raise ValueError("need at least 8 candles")
    asset_class = candles[-1].asset_class
    size = proposed_size if side in {Side.LONG, Side.SHORT} else 0.0
    if asset_class is AssetClass.MAJOR:
        size, note = _major(candles, size)
    elif asset_class is AssetClass.LARGE_CAP_ALT:
        size, note = _alt(candles, size)
    elif asset_class is AssetClass.STABLECOIN:
        size, note = 0.0, _stable(candles)
    elif asset_class is AssetClass.DEFI:
        size, note = _defi(candles, size)
    elif asset_class is AssetClass.MEME:
        size, note = _meme(candles, size)
    elif asset_class is AssetClass.L2:
        size, note = _l2(candles, size)
    elif asset_class is AssetClass.RWA:
        size, note = _rwa(candles, size)
    else:
        size, note = _perpetual(candles, size)
    size = min(size, proposed_size if proposed_size > 0 else 0.0)
    return {
        "symbol": candles[-1].symbol,
        "asset_class": asset_class.value,
        "side": side.value if size > 0 else Side.FLAT.value,
        "size_fraction": round(max(size, 0.0), 6),
        "note": note,
        "guard": LIQUIDITY_NOTES[asset_class.value],
        "stress_budget": STRESS_BUDGET[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    base = float(median(bar.volume for bar in candles[-8:])) or 1.0
    last = candles[-1]
    width = (last.high - last.low) / last.close if last.close else 0.0
    if last.volume < base * 0.4 and width >= 0.015 and size > 0:
        return size * 0.5, "major thin book: volume below 40 percent of median and range above 1.5 percent"
    return size, "major liquidity guard not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    prior = candles[-2].close
    width = (last.high - last.low) / last.close if last.close else 0.0
    close_move = abs(last.close / prior - 1.0) if prior else 0.0
    if width >= 0.05 and close_move <= 0.01 and size > 0:
        return size * 0.5, "large-cap venue chop: range above 5 percent with the close inside 1 percent"
    return size, "large-cap liquidity guard not triggered"


def _stable(candles: list[Candle]) -> str:
    last = candles[-1]
    width = last.high - last.low
    off_peg = abs(last.close - 1.0)
    if width >= 0.0025 and off_peg >= 0.001:
        return "stablecoin redemption stress: range above 25 bp and close at least 10 bp off the peg; size stays zero"
    return "stablecoin liquidity guard not triggered; size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    drops = []
    for index in (-3, -2, -1):
        previous = candles[index - 1].close
        drops.append(previous > 0 and candles[index].close / previous - 1.0 <= -0.015)
    if all(drops):
        return 0.0, "defi cascade: three bars each lost more than 1.5 percent"
    return size, "defi liquidity guard not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    base = float(median(bar.volume for bar in candles[-8:])) or 1.0
    burst = candles[-1].close / candles[-5].close - 1.0 if candles[-5].close else 0.0
    if burst >= 0.10 and candles[-1].volume < base * 0.3:
        return 0.0, "meme liquidity vacuum: 10 percent burst on volume below 30 percent of median"
    return size, "meme liquidity guard not triggered"


def _l2(candles: list[Candle], size: float) -> tuple[float, str]:
    volumes = [bar.volume for bar in candles[-4:]]
    closes = [bar.close for bar in candles[-4:]]
    matched = max(volumes) > 0 and (max(volumes) - min(volumes)) / max(volumes) <= 0.01
    flat = closes[0] > 0 and abs(closes[-1] / closes[0] - 1.0) <= 0.002
    if matched and flat and size > 0:
        return size * 0.5, "l2 sequencer stall: four matched volumes and a flat price"
    return size, "l2 liquidity guard not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    closes = [bar.close for bar in candles[-8:]]
    mean = sum(closes) / len(closes)
    dislocation = abs(candles[-1].close / mean - 1.0) if mean else 0.0
    if dislocation > 0.03 and size > 0:
        return size * 0.5, "rwa nav dislocation: close more than 3 percent from the eight-bar mean"
    return size, "rwa liquidity guard not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    change = abs(candles[-1].funding_rate - candles[-2].funding_rate)
    if change >= 0.0008:
        return 0.0, "perp funding acceleration: funding changed by at least 8 bp"
    return size, "perp liquidity guard not triggered"


def liquidity_desk(rows: list[dict[str, object]]) -> dict[str, object]:
    """Offline liquidity desk. A desk packet is not an order and cannot raise size."""
    material = "|".join(
        f"{row.get('symbol')}:{row.get('asset_class')}:{row.get('size_fraction')}:{row.get('note')}" for row in rows
    )
    digest = hashlib.sha256(material.encode()).hexdigest()
    stressed = [row for row in rows if "not triggered" not in str(row.get("note", ""))]
    gross = round(sum(float(row.get("size_fraction") or 0.0) for row in rows), 6)
    return {
        "version": "0.22.0",
        "cadence": "offline liquidity cycle; no socket",
        "stress_budget": dict(STRESS_BUDGET),
        "rows": rows,
        "stress_count": len(stressed),
        "gross_paper_size": gross,
        "desk_digest": digest,
        "network": False,
        "order_instruction": False,
        "order_path": False,
        "can_increase_size": False,
        "can_enable_live": False,
        "paper_only": True,
    }


def screen_stage(stage: str, action: str) -> dict[str, object]:
    """Decide whether an adversary-path action is allowed. Trade actions are not."""
    known = {item["stage"] for item in KILL_CHAIN}
    if stage not in known:
        raise ValueError("unknown kill-chain stage")
    refused = action in REFUSED_ACTIONS
    return {
        "stage": stage,
        "action": action,
        "allowed": not refused,
        "can_trade": False,
        "can_enable_live": False,
        "reason": "action refused on every stage" if refused else "research action stays inside the paper plane",
    }


def assume_breach_drill() -> dict[str, object]:
    """Paper drill. New size is zero. The drill cannot enable live trading."""
    return {
        "version": "0.22.0",
        "paper_size": 0.0,
        "kill_switch": True,
        "order_path": False,
        "can_enable_live": False,
        "material_stored": False,
        "steps": [
            "set paper size to zero",
            "freeze the audit digest",
            "refuse trade and withdrawal scopes",
            "require a human review before the kill switch is cleared",
        ],
    }


def kill_chain_architecture() -> dict[str, object]:
    """Cyber kill-chain map for the research plane. Rules only. No execution zone."""
    return {
        "version": "0.22.0",
        "framework": "research kill-chain map; not a MITRE, NIST, SOC, or ISO certification",
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "network": False,
        "material_stored": False,
        "stages": list(KILL_CHAIN),
        "refused_actions": list(REFUSED_ACTIONS),
        "controls": [
            {"name": "liquidity_guard", "effect": "asset-class liquidity guards can only shrink paper size"},
            {"name": "desk_digest", "effect": "the liquidity desk publishes an information digest, not an order"},
            {"name": "stage_screen", "effect": "trade, withdrawal, and live-enable actions are refused at every stage"},
            {"name": "assume_breach", "effect": "a breach drill zeroes paper size and cannot enable live trading"},
        ],
        "duties": [
            {"identity": "researcher", "can_emit_desk": True, "can_trade": False, "can_enable_live": False},
            {"identity": "auditor", "can_emit_desk": True, "can_trade": False, "can_enable_live": False},
            {"identity": "operator", "can_emit_desk": False, "can_trade": False, "can_enable_live": False},
            {"identity": "automation_runner", "can_store_secret": False, "can_trade": False, "can_enable_live": False},
        ],
        "principles": [
            "a liquidity guard cannot raise a class size cap",
            "a liquidity-desk digest is an information artifact, not an order",
            "every kill-chain stage refuses trade, withdrawal, and live-enable actions",
            "an assume-breach drill zeroes paper size and stores no key material",
            "there is still no execution zone",
        ],
    }
