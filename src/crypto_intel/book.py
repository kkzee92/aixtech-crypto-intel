"""Book-level paper exposure. Strategies propose; the book can shrink them.

Caps are research limits, not a portfolio mandate. Stablecoin alerts never
consume risk budget.
"""

from __future__ import annotations

from dataclasses import dataclass

from crypto_intel.models import AssetClass, Side, Signal

GROSS_CAP = 0.12
BETA_CLUSTER = frozenset(
    {
        AssetClass.MAJOR,
        AssetClass.LARGE_CAP_ALT,
        AssetClass.DEFI,
        AssetClass.MEME,
        AssetClass.L2,
    }
)
BETA_CAP = 0.10
RWA_CAP = 0.02
PERP_CAP = 0.02


@dataclass(frozen=True)
class Allocation:
    symbol: str
    asset_class: AssetClass
    side: Side
    proposed: float
    allocated: float
    reason: str


def allocate(proposals: list[tuple[Signal, float]]) -> list[Allocation]:
    """Scale positive paper sizes so gross and cluster caps hold.

    `proposals` are already risk-gated sizes. Zero sizes pass through.
    """
    active = [(signal, size) for signal, size in proposals if size > 0 and signal.side in {Side.LONG, Side.SHORT}]
    gross = sum(size for _, size in active)
    beta = sum(size for signal, size in active if signal.asset_class in BETA_CLUSTER)
    rwa = sum(size for signal, size in active if signal.asset_class is AssetClass.RWA)
    perp = sum(size for signal, size in active if signal.asset_class is AssetClass.PERPETUAL)
    scale = 1.0
    notes: list[str] = []
    if gross > GROSS_CAP and gross > 0:
        scale = min(scale, GROSS_CAP / gross)
        notes.append("gross cap")
    if beta > BETA_CAP and beta > 0:
        scale = min(scale, BETA_CAP / beta)
        notes.append("crypto-beta cluster cap")
    if rwa > RWA_CAP and rwa > 0:
        scale = min(scale, RWA_CAP / rwa)
        notes.append("rwa bucket cap")
    if perp > PERP_CAP and perp > 0:
        scale = min(scale, PERP_CAP / perp)
        notes.append("perpetual bucket cap")
    reason = "within book limits" if scale == 1.0 else "scaled: " + ", ".join(notes)
    rows: list[Allocation] = []
    for signal, size in proposals:
        if size <= 0 or signal.side not in {Side.LONG, Side.SHORT}:
            rows.append(Allocation(signal.symbol, signal.asset_class, signal.side, size, 0.0, "no risk budget"))
            continue
        rows.append(
            Allocation(
                signal.symbol,
                signal.asset_class,
                signal.side,
                size,
                round(size * scale, 6),
                reason,
            )
        )
    return rows
