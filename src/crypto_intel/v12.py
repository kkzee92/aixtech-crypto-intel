"""Version 0.12 microstructure guards, strategy cards, and data lineage.

Guards can shrink or refuse a paper size. They cannot raise a class cap, open a
socket, store a secret, or place an order. The lineage report is a research
control map, not a certification and not legal advice.
"""

from __future__ import annotations

import hashlib
from statistics import median

from crypto_intel.models import AssetClass, Candle, Side

MICRO_NOTES: dict[str, str] = {
    AssetClass.MAJOR.value: "participation haircut when the last volume is below 40 percent of the 8-bar median",
    AssetClass.LARGE_CAP_ALT.value: "wick-rejection veto when the upper wick is most of the bar and the close is below the open",
    AssetClass.STABLECOIN.value: "secondary peg watch; size stays zero",
    AssetClass.DEFI.value: "impact haircut when range and volume both expand",
    AssetClass.MEME.value: "climax veto when the last bar range exceeds 12 percent of the close",
    AssetClass.L2.value: "benchmark-lag haircut when the series trails the benchmark by more than 4 percent",
    AssetClass.RWA.value: "thin-print haircut when the last volume is below half the median",
    AssetClass.PERPETUAL.value: "basis-blowout veto when the bar range and funding are both extended",
}

ZONES = (
    {
        "zone": "ingest",
        "allowed": ["synthetic_fixture", "attested_public_print"],
        "refused": ["credential", "seed", "withdrawal_key", "personal_data"],
        "can_trade": False,
    },
    {
        "zone": "research",
        "allowed": ["classified_feature", "paper_signal", "strategy_card"],
        "refused": ["order_instruction", "live_enablement"],
        "can_trade": False,
    },
    {
        "zone": "audit",
        "allowed": ["hash_chain", "redacted_lineage"],
        "refused": ["secret", "personal_data"],
        "can_trade": False,
    },
    {
        "zone": "secrets",
        "allowed": [],
        "refused": ["credential", "seed", "withdrawal_key", "personal_data"],
        "can_trade": False,
    },
)


def apply_v12(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
    benchmark: list[Candle] | None = None,
) -> dict[str, object]:
    """Eighth-pass microstructure guard. Size cannot increase."""
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
        size, note = _l2(candles, size, benchmark)
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
        "guard": MICRO_NOTES[asset_class.value],
        "live_enabled": False,
        "can_increase_size": False,
        "order_path": False,
    }


def _median_volume(candles: list[Candle]) -> float:
    return float(median(bar.volume for bar in candles[-8:]))


def _major(candles: list[Candle], size: float) -> tuple[float, str]:
    base = _median_volume(candles)
    if size > 0 and base > 0 and candles[-1].volume < 0.4 * base:
        return size * 0.5, "major participation haircut"
    return size, "major: participation haircut not triggered"


def _alt(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    span = last.high - last.low
    wick = last.high - max(last.open, last.close)
    rejected = span > 0 and wick / span >= 0.6 and last.close < last.open
    if size > 0 and rejected:
        return 0.0, "large-cap alt wick-rejection veto"
    return size, "large-cap alt: wick-rejection veto not triggered"


def _stable(candles: list[Candle]) -> str:
    last = candles[-1]
    if abs(last.close - 1.0) >= 0.0015:
        return "stablecoin secondary peg watch; size stays zero"
    return "stablecoin: size stays zero"


def _defi(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    base = _median_volume(candles)
    wide = last.close > 0 and (last.high - last.low) / last.close > 0.04
    if size > 0 and wide and base > 0 and last.volume > 1.8 * base:
        return size * 0.5, "defi impact haircut"
    return size, "defi: impact haircut not triggered"


def _meme(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    if size > 0 and last.close > 0 and (last.high - last.low) / last.close > 0.12:
        return 0.0, "meme climax veto"
    return size, "meme: climax veto not triggered"


def _l2(candles: list[Candle], size: float, benchmark: list[Candle] | None) -> tuple[float, str]:
    if not benchmark or len(benchmark) < 8:
        return size, "l2: benchmark missing; lag haircut not applied"
    own = candles[-1].close / candles[-6].close - 1.0
    bench = benchmark[-1].close / benchmark[-6].close - 1.0
    if size > 0 and own - bench < -0.04:
        return size * 0.5, "l2 benchmark-lag haircut"
    return size, "l2: benchmark-lag haircut not triggered"


def _rwa(candles: list[Candle], size: float) -> tuple[float, str]:
    base = _median_volume(candles)
    if size > 0 and base > 0 and candles[-1].volume < 0.5 * base:
        return size * 0.5, "rwa thin-print haircut"
    return size, "rwa: thin-print haircut not triggered"


def _perpetual(candles: list[Candle], size: float) -> tuple[float, str]:
    last = candles[-1]
    wide = last.close > 0 and (last.high - last.low) / last.close > 0.05
    if size > 0 and wide and abs(last.funding_rate) > 0.001:
        return 0.0, "perp basis-blowout veto"
    return size, "perp: basis-blowout veto not triggered"


def strategy_cards(rows: list[dict[str, object]]) -> dict[str, object]:
    """Offline strategy card. It is not an order and cannot raise size."""
    cards = []
    for row in rows:
        asset_class = str(row.get("asset_class", "unknown"))
        cards.append(
            {
                "symbol": row.get("symbol"),
                "asset_class": asset_class,
                "size_fraction": float(row.get("size_fraction", 0.0)),
                "guard": MICRO_NOTES.get(asset_class, "unknown class; size not raised"),
                "order_instruction": False,
            }
        )
    material = "|".join(f"{card['symbol']}:{card['asset_class']}:{card['size_fraction']}" for card in cards)
    return {
        "version": "0.12.0",
        "cards": cards,
        "gross_paper_fraction": round(sum(float(card["size_fraction"]) for card in cards), 6),
        "card_digest": hashlib.sha256(material.encode()).hexdigest(),
        "live_enabled": False,
        "order_path": False,
        "order_instruction": False,
        "can_increase_size": False,
        "paper_only": True,
    }


def lineage_report(source_label: str, fixture_text: str) -> dict[str, object]:
    """Data-lineage and zone map. No secret is accepted or stored."""
    lowered = fixture_text.lower()
    refused = any(token in lowered for token in ("api_key", "seed phrase", "private_key", "nric"))
    digest = hashlib.sha256(fixture_text.encode()).hexdigest()
    return {
        "version": "0.12.0",
        "framework": "research lineage map; not a certification and not legal advice",
        "source_label": source_label,
        "fixture_digest": digest,
        "live_enabled": False,
        "order_path": False,
        "execution_zone": False,
        "zones": list(ZONES),
        "retention": {
            "synthetic_fixture": "repo lifetime; labelled synthetic",
            "credential": "zero",
            "seed": "zero",
            "personal_data": "zero",
            "audit": "hash chain only; secrets redacted before write",
        },
        "transport": {
            "in_transit": "TLS 1.2 or newer if a future public feed is added; none is called by default",
            "at_rest": "AES-256 is the required class for any future store; this tree keeps fixtures in git only",
            "keys_in_git": False,
        },
        "refused_secret_material": refused,
        "principles": [
            "a microstructure guard cannot raise a class size cap",
            "a strategy card is an information artifact, not an order",
            "ingest, research, audit, and secrets zones cannot trade",
            "credentials, seeds, and personal data are refused, not committed",
            "lineage records a digest, not the raw secret",
        ],
    }
