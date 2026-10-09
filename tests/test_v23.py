"""v0.23 flow guards, information bus, and data-flow security plane."""

from pathlib import Path

import pytest

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v23 import apply_v23, data_flow_plane, information_bus, screen_flow


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
                high=price + 0.2,
                low=price - 0.2,
                close=price,
                volume=volume + index,
                funding_rate=funding,
            )
        )
    return rows


def test_major_vol_spike_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR, close=100.0, step=0.0)
    spiked = bars[:-1] + [Candle("TEST", AssetClass.MAJOR, "t", 100, 103, 97, 100, 80)]
    guarded = apply_v23(spiked, proposed_size=0.08, side=Side.LONG)
    assert guarded["size_fraction"] == 0.04
    assert guarded["can_increase_size"] is False
    assert apply_v23(spiked, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01
    quiet = apply_v23(bars, proposed_size=0.08, side=Side.LONG)
    assert quiet["size_fraction"] == 0.08
    assert "not triggered" in str(quiet["note"])


def test_alt_follow_through_and_stable_velocity_stay_bounded() -> None:
    bars = _bars(AssetClass.LARGE_CAP_ALT, close=100.0, step=0.0)
    failed = bars[:-1] + [Candle("TEST", AssetClass.LARGE_CAP_ALT, "t", 100, 102, 97.5, 98.0, 90)]
    assert apply_v23(failed, proposed_size=0.04, side=Side.LONG)["size_fraction"] == 0.02
    stable = _bars(AssetClass.STABLECOIN, close=1.0, step=0.0)
    moving = stable[:-1] + [Candle("TEST", AssetClass.STABLECOIN, "t", 1.0, 1.003, 0.997, 1.002, 40)]
    watched = apply_v23(moving, proposed_size=0.05, side=Side.ALERT)
    assert watched["size_fraction"] == 0.0
    assert "peg velocity" in str(watched["note"])
    calm = apply_v23(stable, proposed_size=0.05, side=Side.ALERT)
    assert calm["size_fraction"] == 0.0
    assert "not triggered" in str(calm["note"])


def test_defi_gap_and_meme_wick_shrink_or_zero() -> None:
    defi = _bars(AssetClass.DEFI, close=100.0, step=0.0)
    gapped = defi[:-1] + [Candle("TEST", AssetClass.DEFI, "t", 103, 103.4, 102.4, 103.1, 70)]
    assert apply_v23(gapped, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01
    meme = _bars(AssetClass.MEME, close=100.0, step=0.0)
    wicked = meme[:-1] + [Candle("TEST", AssetClass.MEME, "t", 100, 110, 99, 101, 80)]
    assert apply_v23(wicked, proposed_size=0.005, side=Side.LONG)["size_fraction"] == 0.0
    held = apply_v23(meme, proposed_size=0.005, side=Side.LONG)
    assert held["size_fraction"] == 0.005


def test_l2_fee_spike_rwa_stale_and_perp_squeeze() -> None:
    l2 = _bars(AssetClass.L2, close=100.0, step=0.0, volume=50)
    spiked = l2[:-1] + [Candle("TEST", AssetClass.L2, "t", 100, 104, 97, 100, 200)]
    assert apply_v23(spiked, proposed_size=0.03, side=Side.LONG)["size_fraction"] == 0.015
    rwa = [Candle("TEST", AssetClass.RWA, f"t{index}", 50, 50.2, 49.8, 50, 40) for index in range(8)]
    assert apply_v23(rwa, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01
    perp = _bars(AssetClass.PERPETUAL, close=100.0, step=0.0, funding=-0.0008)
    squeezed = perp[:-1] + [
        Candle("TEST", AssetClass.PERPETUAL, "t", 104, 104.4, 103.4, 104.2, 80, funding_rate=-0.0008)
    ]
    faded = apply_v23(squeezed, proposed_size=0.02, side=Side.LONG)
    assert faded["size_fraction"] == 0.0
    assert faded["order_path"] is False


def test_quiet_paths_bus_and_flow_plane(capsys) -> None:
    assert "not triggered" in str(
        apply_v23(_bars(AssetClass.LARGE_CAP_ALT), proposed_size=0.04, side=Side.LONG)["note"]
    )
    assert "not triggered" in str(apply_v23(_bars(AssetClass.DEFI), proposed_size=0.02, side=Side.LONG)["note"])
    assert "not triggered" in str(apply_v23(_bars(AssetClass.L2), proposed_size=0.03, side=Side.LONG)["note"])
    assert "not triggered" in str(apply_v23(_bars(AssetClass.RWA), proposed_size=0.02, side=Side.LONG)["note"])
    assert "not triggered" in str(apply_v23(_bars(AssetClass.PERPETUAL), proposed_size=0.02, side=Side.SHORT)["note"])
    from crypto_intel.__main__ import main

    fixture = str(Path(__file__).parents[1] / "fixtures" / "candles_synthetic.json")
    assert main(["flow"]) == 0
    assert main(["bus", fixture]) == 0
    assert main(["v23", fixture]) == 0
    assert main(["killchain"]) == 0
    assert main(["desk", fixture]) == 0
    assert main(["v22", fixture]) == 0
    assert main(["residency"]) == 0
    assert main(["clock", fixture]) == 0
    assert main(["v21", fixture]) == 0
    assert "execution_zone" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        main(["bus"])
    row = apply_v23(_bars(AssetClass.MAJOR), proposed_size=0.04, side=Side.LONG)
    packet = information_bus([row])
    assert packet["paper_only"] is True
    assert packet["can_enable_live"] is False
    assert packet["gross_paper_size"] == 0.04
    assert len(str(packet["bus_digest"])) == 64
    plane = data_flow_plane()
    assert plane["execution_zone"] is False
    assert plane["material_stored"] is False
    assert plane["zones"] == ["ingest", "research", "audit", "egress"]
    allowed = screen_flow("ingest", "research", "public_market")
    assert allowed["allowed"] is True
    assert allowed["can_trade"] is False
    blocked = screen_flow("research", "egress", "secret")
    assert blocked["allowed"] is False
    assert blocked["can_enable_live"] is False
    audit_only = screen_flow("research", "egress", "audit")
    assert audit_only["allowed"] is False
    with pytest.raises(ValueError):
        screen_flow("execution", "egress", "public_market")
    with pytest.raises(ValueError):
        screen_flow("ingest", "research", "payload")
    with pytest.raises(ValueError):
        apply_v23(_bars(AssetClass.MAJOR)[:4], proposed_size=0.01, side=Side.LONG)
