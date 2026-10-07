"""v0.13 venue-fragmentation guards, information mesh, and resilience plane."""

import pytest

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v13 import apply_v13, information_mesh, resilience_plane


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


def test_major_venue_disagreement_haircut_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR)
    wide = bars[:-1] + [Candle("TEST", AssetClass.MAJOR, "2026-01-01T12:00:00Z", 100, 108, 92, 100, 100)]
    row = apply_v13(wide, proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.04
    assert row["can_increase_size"] is False
    assert row["order_path"] is False
    assert row["live_enabled"] is False


def test_major_quiet_range_keeps_size() -> None:
    row = apply_v13(_bars(AssetClass.MAJOR), proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.08
    assert "not triggered" in str(row["note"])


def test_alt_listing_fragmentation_haircut() -> None:
    bars = _bars(AssetClass.LARGE_CAP_ALT, volume=100.0)
    gapped = bars[:-1] + [Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T12:00:00Z", 101, 108, 100, 106, 40)]
    row = apply_v13(gapped, proposed_size=0.04, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "listing-fragmentation" in str(row["note"])


def test_stablecoin_redemption_stress_stays_zero() -> None:
    bars = _bars(AssetClass.STABLECOIN, close=1.0, step=0.0)
    oscillating = bars[:-2] + [
        Candle("TEST", AssetClass.STABLECOIN, "2026-01-01T10:00:00Z", 1.002, 1.003, 1.001, 1.002, 100),
        Candle("TEST", AssetClass.STABLECOIN, "2026-01-01T11:00:00Z", 0.998, 0.999, 0.997, 0.998, 100),
    ]
    row = apply_v13(oscillating, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert row["side"] == "flat"
    assert "redemption-stress" in str(row["note"])


def test_stablecoin_quiet_peg_stays_zero() -> None:
    row = apply_v13(_bars(AssetClass.STABLECOIN, close=1.0, step=0.0), proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "size stays zero" in str(row["note"])


def test_defi_oracle_gap_veto() -> None:
    bars = _bars(AssetClass.DEFI, close=100.0, step=0.0, volume=100.0)
    jumped = bars[:-1] + [Candle("TEST", AssetClass.DEFI, "2026-01-01T12:00:00Z", 100, 108, 99, 107, 40)]
    row = apply_v13(jumped, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "oracle-gap" in str(row["note"])


def test_meme_exhaustion_veto() -> None:
    bars = _bars(AssetClass.MEME, close=100.0, step=0.0)
    exhausted = bars[:-4] + [
        Candle("TEST", AssetClass.MEME, "2026-01-01T08:00:00Z", 100, 101, 99, 100, 100),
        Candle("TEST", AssetClass.MEME, "2026-01-01T09:00:00Z", 109, 110, 108, 109, 100),
        Candle("TEST", AssetClass.MEME, "2026-01-01T10:00:00Z", 107, 108, 106, 107, 100),
        Candle("TEST", AssetClass.MEME, "2026-01-01T11:00:00Z", 105, 106, 104, 105, 100),
    ]
    row = apply_v13(exhausted, proposed_size=0.005, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "exhaustion" in str(row["note"])


def test_l2_sequencer_stall_haircut() -> None:
    bars = _bars(AssetClass.L2, volume=100.0)
    stalled = bars[:-1] + [Candle("TEST", AssetClass.L2, "2026-01-01T12:00:00Z", 100, 100.05, 99.95, 100, 400)]
    row = apply_v13(stalled, proposed_size=0.03, side=Side.LONG)
    assert row["size_fraction"] == 0.015
    assert "sequencer-stall" in str(row["note"])


def test_rwa_stale_attestation_veto() -> None:
    bars = _bars(AssetClass.RWA, close=100.0, step=0.0)
    row = apply_v13(bars, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "stale-attestation" in str(row["note"])


def test_rwa_moving_print_keeps_size() -> None:
    row = apply_v13(_bars(AssetClass.RWA, close=100.0, step=0.2), proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "not triggered" in str(row["note"])


def test_perp_funding_price_disagreement_haircut() -> None:
    bars = _bars(AssetClass.PERPETUAL, close=100.0, step=0.0, funding=-0.0008)
    moved = bars[:-1] + [Candle("TEST", AssetClass.PERPETUAL, "2026-01-01T12:00:00Z", 100, 103, 99, 102, 100, -0.0008)]
    row = apply_v13(moved, proposed_size=0.02, side=Side.SHORT)
    assert row["size_fraction"] == 0.01
    assert "disagreement" in str(row["note"])


def test_perp_aligned_funding_keeps_size() -> None:
    bars = _bars(AssetClass.PERPETUAL, close=100.0, step=0.0, funding=0.0008)
    moved = bars[:-1] + [Candle("TEST", AssetClass.PERPETUAL, "2026-01-01T12:00:00Z", 100, 103, 99, 102, 100, 0.0008)]
    row = apply_v13(moved, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "not triggered" in str(row["note"])


def test_flat_side_stays_zero() -> None:
    row = apply_v13(_bars(AssetClass.MAJOR), proposed_size=0.08, side=Side.FLAT)
    assert row["size_fraction"] == 0.0


def test_short_series_is_refused() -> None:
    with pytest.raises(ValueError, match="8 candles"):
        apply_v13(_bars(AssetClass.MAJOR)[:4], proposed_size=0.08, side=Side.LONG)


def test_mesh_disagreement_shrinks_and_cannot_order() -> None:
    mesh = information_mesh(
        [
            {
                "symbol": "BTC-USD",
                "asset_class": "major",
                "primary_close": 100.0,
                "secondary_close": 108.0,
                "size_fraction": 0.08,
            },
            {
                "symbol": "USDC-USD",
                "asset_class": "stablecoin",
                "primary_close": 1.0,
                "secondary_close": 1.0,
                "size_fraction": 0.0,
            },
        ]
    )
    assert mesh["network"] is False
    assert mesh["order_instruction"] is False
    assert mesh["can_increase_size"] is False
    assert mesh["rows"][0]["contested"] is True
    assert mesh["rows"][0]["size_fraction"] == 0.04
    assert mesh["rows"][1]["contested"] is False
    assert mesh["mesh_digest"]


def test_mesh_cannot_raise_a_zero_size() -> None:
    mesh = information_mesh(
        [{"symbol": "DOGE-USD", "asset_class": "meme", "primary_close": 1.0, "secondary_close": 1.2, "size_fraction": 0.0}]
    )
    assert mesh["rows"][0]["size_fraction"] == 0.0
    assert mesh["rows"][0]["contested"] is True


def test_resilience_plane_has_no_execution_zone() -> None:
    plane = resilience_plane()
    assert plane["execution_zone"] is False
    assert plane["backup"]["seed_backup"] is False
    assert plane["backup"]["can_restore_live_trading"] is False
    assert plane["quorum"]["can_enable_live"] is False
    assert {item["function"] for item in plane["functions"]} == {"identify", "protect", "detect", "respond", "recover"}
    trade = next(item for item in plane["key_scopes"] if item["scope"] == "trade")
    assert trade["refused"] is True
    assert trade["stored_in_tree"] is False
    operator = next(item for item in plane["separation_of_duties"] if item["role"] == "operator")
    assert operator["can_read_mesh"] is False
    assert operator["can_enable_live"] is False
    assert "private_key" in plane["data_plane"]["refused"]
    assert "production_custody" in plane["data_residency"]["refused"]
