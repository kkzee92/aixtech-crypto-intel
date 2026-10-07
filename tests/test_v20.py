"""v0.20 inventory-age guards, information dispatch, and disclosure boundary."""

import pytest

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v20 import apply_v20, disclosure_boundary, information_dispatch, screen_zone


def _bars(
    asset_class: AssetClass,
    *,
    volume: float = 100.0,
    funding: float = 0.0,
    close: float = 100.0,
    step: float = 0.1,
) -> list[Candle]:
    rows = []
    for index in range(12):
        price = close + index * step
        rows.append(
            Candle(
                symbol="TEST",
                asset_class=asset_class,
                timestamp=f"2026-01-01T{index:02d}:00:00Z",
                open=price,
                high=price + 1,
                low=price - 1,
                close=price,
                volume=volume + index,
                funding_rate=funding,
            )
        )
    return rows


def test_major_drought_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR)
    quiet = [
        Candle(bar.symbol, bar.asset_class, bar.timestamp, bar.open, bar.high, bar.low, bar.close, 10.0)
        if index >= 9
        else bar
        for index, bar in enumerate(bars)
    ]
    guarded = apply_v20(quiet, proposed_size=0.08, side=Side.LONG)
    assert guarded["size_fraction"] == 0.04
    assert guarded["can_increase_size"] is False
    assert apply_v20(quiet, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01


def test_alt_follow_through_and_stable_stay_bounded() -> None:
    bars = _bars(AssetClass.LARGE_CAP_ALT, close=100.0, step=0.0)
    failed = bars[:-1] + [Candle("TEST", AssetClass.LARGE_CAP_ALT, "t", 99, 100, 98, 98, 100)]
    assert apply_v20(failed, proposed_size=0.04, side=Side.LONG)["size_fraction"] == 0.02
    stable = _bars(AssetClass.STABLECOIN, close=1.003, step=0.0)
    watched = apply_v20(stable, proposed_size=0.05, side=Side.ALERT)
    assert watched["size_fraction"] == 0.0
    assert "peg-persistence" in str(watched["note"])


def test_meme_fade_and_funding_flip_zero_size() -> None:
    meme = _bars(AssetClass.MEME, close=100.0, step=0.0)
    faded = meme[:-1] + [Candle("TEST", AssetClass.MEME, "t", 120, 130, 110, 112, 50)]
    assert apply_v20(faded, proposed_size=0.005, side=Side.LONG)["size_fraction"] == 0.0
    perp = _bars(AssetClass.PERPETUAL, funding=-0.001)
    flipped_bars = perp[:-1] + [
        Candle("TEST", AssetClass.PERPETUAL, "t", 101, 102, 100, 101, 110, funding_rate=0.001)
    ]
    flipped = apply_v20(flipped_bars, proposed_size=0.02, side=Side.LONG)
    assert flipped["size_fraction"] == 0.0
    assert flipped["order_path"] is False


def test_dispatch_and_boundary_cannot_trade() -> None:
    row = apply_v20(_bars(AssetClass.RWA), proposed_size=0.02, side=Side.LONG)
    packet = information_dispatch([row])
    assert packet["paper_only"] is True
    assert packet["can_enable_live"] is False
    assert len(str(packet["dispatch_digest"])) == 64
    plane = disclosure_boundary()
    assert plane["execution_zone"] is False
    assert plane["material_stored"] is False
    public = screen_zone("public_brief", "BTC paper size 0.02")
    assert public["size_included"] is False
    blocked = screen_zone("audit", "exchange trade key pasted")
    assert blocked["allowed"] is False
    with pytest.raises(ValueError):
        screen_zone("live", "nope")
