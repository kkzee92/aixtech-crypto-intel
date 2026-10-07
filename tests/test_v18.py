"""v0.18 microstructure guards, information wire, and API plane."""

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v18 import apply_v18, api_plane, information_wire


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


def test_major_spread_proxy_haircut_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR, close=100.0, step=0.0, volume=100.0)
    wide = bars[:-1] + [
        Candle("TEST", AssetClass.MAJOR, "2026-01-01T11:00:00Z", 100, 102, 98, 100, 50),
    ]
    row = apply_v18(wide, proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.04
    assert row["can_increase_size"] is False
    assert row["order_path"] is False
    assert row["live_enabled"] is False
    assert "spread-proxy" in str(row["note"])


def test_major_quiet_path_keeps_size() -> None:
    row = apply_v18(_bars(AssetClass.MAJOR), proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.08
    assert "not triggered" in str(row["note"])


def test_alt_failed_hold_veto() -> None:
    bars = _bars(AssetClass.LARGE_CAP_ALT, close=100.0, step=0.0)
    failed = bars[:-2] + [
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T10:00:00Z", 100, 101, 99, 101, 100),
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T11:00:00Z", 101, 101.2, 99, 99.5, 100),
    ]
    row = apply_v18(failed, proposed_size=0.04, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "failed-hold" in str(row["note"])


def test_stablecoin_widening_peg_stays_zero() -> None:
    bars = _bars(AssetClass.STABLECOIN, close=1.0, step=0.0)
    widening = bars[:-3] + [
        Candle("TEST", AssetClass.STABLECOIN, "2026-01-01T09:00:00Z", 1.0, 1.003, 0.999, 1.002, 100),
        Candle("TEST", AssetClass.STABLECOIN, "2026-01-01T10:00:00Z", 1.002, 1.005, 1.0, 1.004, 100),
        Candle("TEST", AssetClass.STABLECOIN, "2026-01-01T11:00:00Z", 1.004, 1.008, 1.002, 1.007, 100),
    ]
    row = apply_v18(widening, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "widening-peg" in str(row["note"])


def test_defi_dislocation_veto() -> None:
    bars = _bars(AssetClass.DEFI, close=100.0, step=0.0)
    jumped = bars[:-1] + [
        Candle("TEST", AssetClass.DEFI, "2026-01-01T11:00:00Z", 100, 106, 99, 105, 100),
    ]
    row = apply_v18(jumped, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "dislocation" in str(row["note"])


def test_meme_blowoff_veto() -> None:
    bars = _bars(AssetClass.MEME, volume=100.0)
    blowoff = bars[:-1] + [
        Candle("TEST", AssetClass.MEME, "2026-01-01T11:00:00Z", 110, 112, 100, 101, 900),
    ]
    row = apply_v18(blowoff, proposed_size=0.005, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "blow-off" in str(row["note"])


def test_l2_sequencer_gap_haircut() -> None:
    bars = _bars(AssetClass.L2, close=100.0, step=0.0)
    gapped = bars[:-1] + [
        Candle("TEST", AssetClass.L2, "2026-01-01T11:00:00Z", 103, 103.2, 102.5, 103, 100),
    ]
    row = apply_v18(gapped, proposed_size=0.03, side=Side.LONG)
    assert row["size_fraction"] == 0.015
    assert "sequencer-gap" in str(row["note"])


def test_rwa_too_fast_veto() -> None:
    bars = _bars(AssetClass.RWA, close=100.0, step=0.0)
    fast = bars[:-1] + [
        Candle("TEST", AssetClass.RWA, "2026-01-01T11:00:00Z", 104, 104.2, 103.8, 104, 100),
    ]
    row = apply_v18(fast, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "too-fast" in str(row["note"])


def test_perp_funding_acceleration_haircut() -> None:
    bars = _bars(AssetClass.PERPETUAL, funding=0.0)
    accelerated = bars[:-1] + [
        Candle("TEST", AssetClass.PERPETUAL, "2026-01-01T11:00:00Z", 101, 101.2, 100.8, 101, 100, 0.001),
    ]
    row = apply_v18(accelerated, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.01
    assert "funding-acceleration" in str(row["note"])


def test_wire_and_api_plane_have_no_order_path() -> None:
    row = apply_v18(_bars(AssetClass.MAJOR), proposed_size=0.04, side=Side.LONG)
    wire = information_wire([row])
    assert wire["order_path"] is False
    assert wire["network"] is False
    assert len(str(wire["wire_digest"])) == 64
    plane = api_plane()
    assert plane["execution_zone"] is False
    assert plane["scopes"]["withdrawal_allowlist"] == []
    assert "trade" in plane["scopes"]["refused"]
    assert plane["scopes"]["read_key_can_sign"] is False
    assert plane["live_enabled"] is False
