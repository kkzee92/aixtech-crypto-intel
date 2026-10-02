"""Cross-asset information overlays. Paper research only.

A single-symbol rule can be valid and still be the wrong book decision when
the benchmark is in stress or several stables leave the peg together.
"""

from __future__ import annotations

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.regime import Regime, classify

BETA_CLUSTER = {
    AssetClass.MAJOR,
    AssetClass.LARGE_CAP_ALT,
    AssetClass.DEFI,
    AssetClass.MEME,
    AssetClass.L2,
    AssetClass.PERPETUAL,
}
BREADTH_HALT = 0.5


def benchmark_symbol(grouped: dict[str, list[Candle]]) -> str | None:
    if "BTC-USD" in grouped:
        return "BTC-USD"
    for symbol, series in grouped.items():
        if series and series[-1].asset_class is AssetClass.MAJOR:
            return symbol
    return None


def stablecoin_alerts(grouped: dict[str, list[Candle]]) -> list[str]:
    alerts = []
    for symbol, series in grouped.items():
        if not series or series[-1].asset_class is not AssetClass.STABLECOIN:
            continue
        if abs(series[-1].close - 1.0) >= 0.002:
            alerts.append(symbol)
    return alerts


def stress_fraction(grouped: dict[str, list[Candle]]) -> float:
    checked = 0
    stressed = 0
    for series in grouped.values():
        if len(series) < 8 or series[-1].asset_class is AssetClass.STABLECOIN:
            continue
        checked += 1
        if classify(series) is Regime.STRESS:
            stressed += 1
    if checked == 0:
        return 0.0
    return stressed / checked


def basket_report(grouped: dict[str, list[Candle]]) -> dict[str, object]:
    """Book-level information. Does not place an order."""
    symbol = benchmark_symbol(grouped)
    benchmark_regime = "missing"
    if symbol and len(grouped[symbol]) >= 8:
        benchmark_regime = classify(grouped[symbol]).value
    alerts = stablecoin_alerts(grouped)
    breadth = stress_fraction(grouped)
    return {
        "benchmark": symbol,
        "benchmark_regime": benchmark_regime,
        "beta_spillover": benchmark_regime == Regime.STRESS.value,
        "stablecoin_alerts": alerts,
        "stablecoin_contagion": len(alerts) >= 2,
        "stress_fraction": round(breadth, 4),
        "breadth_halt": breadth >= BREADTH_HALT,
        "live_enabled": False,
    }


def apply_cross_overlay(
    row: dict[str, object],
    report: dict[str, object],
) -> dict[str, object]:
    """Zero directional paper size when the book overlay vetoes the idea."""
    updated = dict(row)
    notes = list(updated.get("notes") or [])
    asset_class = str(updated.get("asset_class"))
    side = str(updated.get("side"))
    veto = None
    if report["breadth_halt"] and side in {Side.LONG.value, Side.SHORT.value}:
        veto = "breadth halt: half or more of non-stable series are in stress"
    elif report["beta_spillover"] and asset_class in {item.value for item in BETA_CLUSTER}:
        if side in {Side.LONG.value, Side.SHORT.value}:
            veto = "beta spillover: benchmark regime is stress"
    elif report["stablecoin_contagion"] and asset_class == AssetClass.STABLECOIN.value:
        veto = "stablecoin contagion: two or more peg watches"
    if veto:
        updated["size_fraction"] = 0.0
        if side in {Side.LONG.value, Side.SHORT.value}:
            updated["side"] = Side.FLAT.value
        notes.append(veto)
        updated["notes"] = notes
        updated["cross_veto"] = veto
    else:
        updated["cross_veto"] = None
    updated["live_enabled"] = False
    return updated
