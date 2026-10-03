"""Per-class liquidity and session gates.

Each rule can shrink or refuse a paper size. None can raise a class cap, open
a socket, or place an order. A wide bar range is a slippage proxy, not a quote.
"""

from __future__ import annotations

from statistics import median

from crypto_intel.catalog import OVERLAYS
from crypto_intel.models import AssetClass, Candle, Side

_RULES = OVERLAYS["liquidity"]


def apply_liquidity_gate(
    candles: list[Candle],
    *,
    proposed_size: float,
    side: Side,
) -> dict[str, object]:
    """Third-pass research rule. Size can only fall."""
    if len(candles) < 8:
        raise ValueError("need at least 8 candles")
    asset_class = candles[-1].asset_class
    size = proposed_size if side in {Side.LONG, Side.SHORT} else 0.0
    note = "liquidity gate: unchanged"
    if asset_class is AssetClass.MAJOR:
        size, note = _participation(candles, size, 0.5, "major thin tape")
    elif asset_class is AssetClass.LARGE_CAP_ALT:
        size, note = _range_veto(candles, size, float(_RULES["alt_range_veto"]), "large-cap alt wide range")
    elif asset_class is AssetClass.STABLECOIN:
        size, note = 0.0, "stablecoin: liquidity gate keeps size at zero"
    elif asset_class is AssetClass.DEFI:
        size, note = _range_veto(candles, size, float(_RULES["defi_slippage_proxy"]), "defi slippage proxy")
    elif asset_class is AssetClass.MEME:
        size, note = _floor(candles, size, float(_RULES["meme_volume_floor"]), "meme thin print")
    elif asset_class is AssetClass.L2:
        size, note = _participation(candles, size, 0.6, "l2 thin relative tape")
    elif asset_class is AssetClass.RWA:
        size, note = _participation(candles, size, 0.5, "rwa off-session proxy")
    else:
        size, note = _crowded_perp(candles, size)
    size = min(size, proposed_size)
    return {
        "symbol": candles[-1].symbol,
        "asset_class": asset_class.value,
        "side": side.value if size > 0 else Side.FLAT.value,
        "size_fraction": round(max(size, 0.0), 6),
        "note": note,
        "live_enabled": False,
        "can_increase_size": False,
    }


def _participation(candles: list[Candle], size: float, ratio: float, label: str) -> tuple[float, str]:
    volumes = [c.volume for c in candles[-8:]]
    base = median(volumes[:-1]) or 1.0
    if volumes[-1] < base * ratio and size > 0:
        return size * 0.5, f"{label}: last volume below {ratio:.1f}x median"
    return size, f"{label}: not triggered"


def _range_veto(candles: list[Candle], size: float, ceiling: float, label: str) -> tuple[float, str]:
    last = candles[-1]
    bar_range = (last.high - last.low) / last.close if last.close else 0.0
    if bar_range > ceiling and size > 0:
        return 0.0, f"{label}: range {bar_range:.4f} above {ceiling:.4f}"
    return size, f"{label}: not triggered"


def _floor(candles: list[Candle], size: float, floor: float, label: str) -> tuple[float, str]:
    if candles[-1].volume < floor and size > 0:
        return 0.0, f"{label}: volume below {floor:.0f}"
    return size, f"{label}: not triggered"


def _crowded_perp(candles: list[Candle], size: float) -> tuple[float, str]:
    volumes = [c.volume for c in candles[-8:]]
    base = median(volumes[:-1]) or 1.0
    funding = abs(candles[-1].funding_rate)
    if funding >= float(_RULES["perp_crowd_funding"]) and volumes[-1] > base * 2 and size > 0:
        return size * 0.5, "perp crowded tape: funding and volume together"
    return size, "perp crowded tape: not triggered"
