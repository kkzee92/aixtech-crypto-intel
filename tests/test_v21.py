"""v0.21 calendar guards, research clock, and data-residency plane."""

import pytest

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v21 import apply_v21, data_residency_plane, research_clock, screen_transfer


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


def test_major_session_gap_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR)
    prior = bars[-2].close
    gapped = bars[:-1] + [
        Candle("TEST", AssetClass.MAJOR, "t", prior * 1.02, prior * 1.03, prior * 1.01, prior * 1.021, 120)
    ]
    guarded = apply_v21(gapped, proposed_size=0.08, side=Side.LONG)
    assert guarded["size_fraction"] == 0.04
    assert guarded["can_increase_size"] is False
    assert apply_v21(gapped, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01


def test_alt_shock_and_stable_acceleration_stay_bounded() -> None:
    bars = _bars(AssetClass.LARGE_CAP_ALT, close=100.0, step=0.0)
    shock = bars[:-2] + [
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "t1", 100, 104, 99, 103.5, 110),
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "t2", 103.5, 112, 103, 110.5, 140),
    ]
    assert apply_v21(shock, proposed_size=0.04, side=Side.LONG)["size_fraction"] == 0.02
    stable = _bars(AssetClass.STABLECOIN, close=1.0, step=0.0)
    accelerated = stable[:-2] + [
        Candle("TEST", AssetClass.STABLECOIN, "t1", 1.0, 1.002, 0.999, 1.001, 100),
        Candle("TEST", AssetClass.STABLECOIN, "t2", 1.001, 1.006, 1.0, 1.004, 100),
    ]
    watched = apply_v21(accelerated, proposed_size=0.05, side=Side.ALERT)
    assert watched["size_fraction"] == 0.0
    assert "peg acceleration" in str(watched["note"])


def test_meme_wick_and_basis_stress_zero_size() -> None:
    meme = _bars(AssetClass.MEME, close=100.0, step=0.0)
    rejected = meme[:-1] + [Candle("TEST", AssetClass.MEME, "t", 100, 112, 99, 102, 180)]
    assert apply_v21(rejected, proposed_size=0.005, side=Side.LONG)["size_fraction"] == 0.0
    perp = _bars(AssetClass.PERPETUAL, close=100.0, step=-0.8, funding=0.001)
    stressed = apply_v21(perp, proposed_size=0.02, side=Side.SHORT)
    assert stressed["size_fraction"] == 0.0
    assert stressed["order_path"] is False


def test_rwa_stale_print_and_l2_fade_halve() -> None:
    rwa = _bars(AssetClass.RWA, close=50.0, step=0.0)
    assert apply_v21(rwa, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01
    l2 = _bars(AssetClass.L2, close=100.0, step=1.0)
    faded = l2[:-1] + [Candle("TEST", AssetClass.L2, "t", 110, 111, 104, 105, 90)]
    assert apply_v21(faded, proposed_size=0.03, side=Side.LONG)["size_fraction"] == 0.015


def test_clock_and_residency_cannot_trade() -> None:
    row = apply_v21(_bars(AssetClass.DEFI), proposed_size=0.02, side=Side.LONG)
    packet = research_clock([row])
    assert packet["paper_only"] is True
    assert packet["can_enable_live"] is False
    assert len(str(packet["clock_digest"])) == 64
    plane = data_residency_plane()
    assert plane["execution_zone"] is False
    assert plane["material_stored"] is False
    assert set(plane["key_roles"]) == {"data_encryption", "audit_sign", "break_glass"}
    local = screen_transfer("public_redacted", "SG", "EU")
    assert local["allowed"] is True
    blocked = screen_transfer("secret", "SG", "EU")
    assert blocked["allowed"] is False
    assert blocked["can_enable_live"] is False
    with pytest.raises(ValueError):
        screen_transfer("wallet", "SG", "EU")
