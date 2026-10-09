"""v0.22 liquidity guards, liquidity desk, and cyber kill-chain plane."""

from pathlib import Path

import pytest

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v22 import apply_v22, assume_breach_drill, kill_chain_architecture, liquidity_desk, screen_stage


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


def test_major_thin_book_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR, volume=100.0, close=100.0, step=0.0)
    thin = bars[:-1] + [Candle("TEST", AssetClass.MAJOR, "t", 100, 102, 98.2, 100, 10)]
    guarded = apply_v22(thin, proposed_size=0.08, side=Side.LONG)
    assert guarded["size_fraction"] == 0.04
    assert guarded["can_increase_size"] is False
    assert apply_v22(thin, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01
    quiet = apply_v22(bars, proposed_size=0.08, side=Side.LONG)
    assert quiet["size_fraction"] == 0.08
    assert "not triggered" in str(quiet["note"])


def test_alt_chop_and_stable_redemption_stay_bounded() -> None:
    bars = _bars(AssetClass.LARGE_CAP_ALT, close=100.0, step=0.0)
    chopped = bars[:-1] + [Candle("TEST", AssetClass.LARGE_CAP_ALT, "t", 100, 106, 94, 100.4, 140)]
    assert apply_v22(chopped, proposed_size=0.04, side=Side.LONG)["size_fraction"] == 0.02
    stable = _bars(AssetClass.STABLECOIN, close=1.0, step=0.0)
    stressed = stable[:-1] + [Candle("TEST", AssetClass.STABLECOIN, "t", 1.0, 1.004, 0.998, 1.002, 80)]
    watched = apply_v22(stressed, proposed_size=0.05, side=Side.ALERT)
    assert watched["size_fraction"] == 0.0
    assert "redemption stress" in str(watched["note"])
    calm = apply_v22(stable, proposed_size=0.05, side=Side.ALERT)
    assert calm["size_fraction"] == 0.0
    assert "not triggered" in str(calm["note"])


def test_defi_cascade_and_meme_vacuum_zero_size() -> None:
    defi = _bars(AssetClass.DEFI, close=100.0, step=0.0)
    cascade = defi[:-3] + [
        Candle("TEST", AssetClass.DEFI, "t1", 100, 100.2, 97.8, 98.0, 90),
        Candle("TEST", AssetClass.DEFI, "t2", 98, 98.2, 95.8, 96.2, 90),
        Candle("TEST", AssetClass.DEFI, "t3", 96.2, 96.4, 94.0, 94.4, 90),
    ]
    assert apply_v22(cascade, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.0
    meme = _bars(AssetClass.MEME, close=100.0, step=0.0)
    vacuum = meme[:-1] + [Candle("TEST", AssetClass.MEME, "t", 110, 112, 109, 111, 5)]
    assert apply_v22(vacuum, proposed_size=0.005, side=Side.LONG)["size_fraction"] == 0.0
    held = apply_v22(meme, proposed_size=0.005, side=Side.LONG)
    assert held["size_fraction"] == 0.005


def test_l2_stall_rwa_dislocation_and_funding_acceleration() -> None:
    l2 = [Candle("TEST", AssetClass.L2, f"t{index}", 100, 100.2, 99.8, 100, 80) for index in range(8)]
    stalled = apply_v22(l2, proposed_size=0.03, side=Side.LONG)
    assert stalled["size_fraction"] == 0.015
    rwa = _bars(AssetClass.RWA, close=50.0, step=0.0)
    dislocated = rwa[:-1] + [Candle("TEST", AssetClass.RWA, "t", 50, 53, 49.8, 52.2, 40)]
    assert apply_v22(dislocated, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01
    perp = _bars(AssetClass.PERPETUAL, funding=0.0)
    jumped = perp[:-1] + [Candle("TEST", AssetClass.PERPETUAL, "t", 101, 101.2, 100.8, 101, 80, funding_rate=0.001)]
    faded = apply_v22(jumped, proposed_size=0.02, side=Side.SHORT)
    assert faded["size_fraction"] == 0.0
    assert faded["order_path"] is False


def test_quiet_paths_and_module_commands(capsys) -> None:
    quiet = _bars(AssetClass.LARGE_CAP_ALT)
    assert "not triggered" in str(apply_v22(quiet, proposed_size=0.04, side=Side.LONG)["note"])
    assert "not triggered" in str(apply_v22(_bars(AssetClass.DEFI), proposed_size=0.02, side=Side.LONG)["note"])
    assert "not triggered" in str(apply_v22(_bars(AssetClass.L2), proposed_size=0.03, side=Side.LONG)["note"])
    assert "not triggered" in str(apply_v22(_bars(AssetClass.RWA), proposed_size=0.02, side=Side.LONG)["note"])
    assert "not triggered" in str(apply_v22(_bars(AssetClass.PERPETUAL), proposed_size=0.02, side=Side.SHORT)["note"])
    from crypto_intel.__main__ import main

    fixture = str(Path(__file__).parents[1] / "fixtures" / "candles_synthetic.json")
    assert main(["killchain"]) == 0
    assert main(["desk", fixture]) == 0
    assert main(["v22", fixture]) == 0
    assert main(["residency"]) == 0
    assert main(["datasec"]) == 0
    assert main(["clock", fixture]) == 0
    assert main(["v21", fixture]) == 0
    assert main(["console", fixture]) == 0
    assert main(["v18", fixture]) == 0
    assert main(["scan", fixture]) == 0
    assert "execution_zone" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        main(["desk"])
    row = apply_v22(_bars(AssetClass.MAJOR), proposed_size=0.04, side=Side.LONG)
    packet = liquidity_desk([row])
    assert packet["paper_only"] is True
    assert packet["can_enable_live"] is False
    assert packet["gross_paper_size"] == 0.04
    assert len(str(packet["desk_digest"])) == 64
    plane = kill_chain_architecture()
    assert plane["execution_zone"] is False
    assert plane["material_stored"] is False
    assert len(plane["stages"]) == 7
    allowed = screen_stage("reconnaissance", "read_audit")
    assert allowed["allowed"] is True
    assert allowed["can_trade"] is False
    blocked = screen_stage("impact", "enable_live")
    assert blocked["allowed"] is False
    assert blocked["can_enable_live"] is False
    drill = assume_breach_drill()
    assert drill["paper_size"] == 0.0
    assert drill["can_enable_live"] is False
    with pytest.raises(ValueError):
        screen_stage("payload", "read_audit")
    with pytest.raises(ValueError):
        apply_v22(_bars(AssetClass.MAJOR)[:4], proposed_size=0.01, side=Side.LONG)
