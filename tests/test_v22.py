"""v0.22 depth-quality guards and provenance plane."""

import pytest

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v22 import apply_v22, attest_provenance, custody_chain, provenance_plane, screen_handoff


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


def test_major_stop_run_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR)
    last = bars[-1]
    wide = bars[:-1] + [
        Candle("TEST", AssetClass.MAJOR, "t", last.open, last.open + 8, last.open - 8, last.close, 140)
    ]
    guarded = apply_v22(wide, proposed_size=0.08, side=Side.LONG)
    assert guarded["size_fraction"] == 0.04
    assert guarded["can_increase_size"] is False
    assert apply_v22(wide, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01
    assert apply_v22(bars, proposed_size=0.08, side=Side.FLAT)["size_fraction"] == 0.0


def test_failed_auction_and_wash_print() -> None:
    alt = _bars(AssetClass.LARGE_CAP_ALT)
    prior_high = max(bar.high for bar in alt[-6:-1])
    failed = alt[:-1] + [
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "t", prior_high, prior_high + 2, prior_high - 1, prior_high - 0.2, 200)
    ]
    assert apply_v22(failed, proposed_size=0.04, side=Side.LONG)["size_fraction"] == 0.02
    meme = _bars(AssetClass.MEME, volume=100)
    wash = meme[:-1] + [Candle("TEST", AssetClass.MEME, "t", 100, 110, 90, 100.4, 900)]
    assert apply_v22(wash, proposed_size=0.005, side=Side.LONG)["size_fraction"] == 0.0


def test_stable_defi_l2_rwa_and_perp() -> None:
    stable = _bars(AssetClass.STABLECOIN, close=1.0, step=0.0)
    watched = stable[:-2] + [
        Candle("TEST", AssetClass.STABLECOIN, "t1", 1.003, 1.004, 1.002, 1.003, 50),
        Candle("TEST", AssetClass.STABLECOIN, "t2", 1.004, 1.005, 1.003, 1.004, 50),
    ]
    assert apply_v22(watched, proposed_size=0.05, side=Side.ALERT)["size_fraction"] == 0.0
    defi = _bars(AssetClass.DEFI, volume=200)
    vacuum = defi[:-1] + [Candle("TEST", AssetClass.DEFI, "t", 100, 106, 94, 103, 40)]
    assert apply_v22(vacuum, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01
    l2 = _bars(AssetClass.L2, close=100, step=0)
    faded = l2[:-7] + [
        Candle("TEST", AssetClass.L2, "a", 100, 101, 99, 100, 10),
        Candle("TEST", AssetClass.L2, "b", 101, 102, 100, 101, 10),
        Candle("TEST", AssetClass.L2, "c", 102, 103, 101, 102, 10),
        Candle("TEST", AssetClass.L2, "d", 104, 105, 103, 104, 10),
        Candle("TEST", AssetClass.L2, "e", 103, 104, 102, 103, 10),
        Candle("TEST", AssetClass.L2, "f", 102, 103, 101, 102, 10),
        Candle("TEST", AssetClass.L2, "g", 101, 102, 100, 101, 10),
    ]
    assert apply_v22(faded, proposed_size=0.03, side=Side.LONG)["size_fraction"] == 0.015
    rwa = _bars(AssetClass.RWA, volume=80)
    gapped = rwa[:-1] + [Candle("TEST", AssetClass.RWA, "t", 104, 105, 103, 104.2, 10)]
    assert apply_v22(gapped, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01
    perp = _bars(AssetClass.PERPETUAL, funding=-0.001)
    flipped = perp[:-1] + [
        Candle("TEST", AssetClass.PERPETUAL, "t", 100, 101, 99, 100, 20, funding_rate=0.001)
    ]
    assert apply_v22(flipped, proposed_size=0.02, side=Side.SHORT)["size_fraction"] == 0.0


def test_provenance_plane_refuses_execution_and_secrets() -> None:
    plane = provenance_plane()
    assert plane["live_enabled"] is False
    assert plane["execution_zone"] is False
    assert plane["material_stored"] is False
    assert all(duty["can_trade"] is False for duty in plane["duties"])
    digest = attest_provenance("SYNTHETIC", "BTC-USD", "collector", "reviewer")
    assert len(digest) == 64
    with pytest.raises(PermissionError):
        attest_provenance("SYNTHETIC", "BTC-USD", "trade-bot", "reviewer")
    with pytest.raises(ValueError):
        attest_provenance("LIVE", "BTC-USD", "collector", "reviewer")
    assert screen_handoff("secret", "reviewed")["allowed"] is False
    assert screen_handoff("research_series", "execution")["allowed"] is False
    assert screen_handoff("research_series", "published")["allowed"] is True
    chain = custody_chain([{"symbol": "BTC-USD", "size_fraction": 0.04, "note": "major depth guard not triggered"}])
    assert chain["order_path"] is False
    assert len(chain["digest"]) == 64


def test_short_series_rejected() -> None:
    with pytest.raises(ValueError):
        apply_v22(_bars(AssetClass.MAJOR)[:3], proposed_size=0.02, side=Side.LONG)
