"""v0.12 basis guards, information desk, and custody plane."""

import pytest

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v12 import apply_v12, custody_plane, information_desk


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


def test_major_basis_flip_haircut_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR, funding=0.0001)
    flipped = bars[:-3] + [
        Candle("TEST", AssetClass.MAJOR, "2026-01-01T09:00:00Z", 100, 101, 99, 100, 100, 0.0002),
        Candle("TEST", AssetClass.MAJOR, "2026-01-01T10:00:00Z", 100, 101, 99, 100, 100, -0.0002),
        Candle("TEST", AssetClass.MAJOR, "2026-01-01T11:00:00Z", 100, 101, 99, 100, 100, 0.0001),
    ]
    row = apply_v12(flipped, proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.04
    assert row["can_increase_size"] is False
    assert row["order_path"] is False
    assert row["live_enabled"] is False


def test_major_stable_funding_keeps_size() -> None:
    row = apply_v12(_bars(AssetClass.MAJOR, funding=0.0001), proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.08
    assert "not triggered" in str(row["note"])


def test_alt_thin_participation_haircut() -> None:
    bars = _bars(AssetClass.LARGE_CAP_ALT, volume=100.0)
    thin = bars[:-1] + [Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T12:00:00Z", 101, 102, 100, 101, 20)]
    row = apply_v12(thin, proposed_size=0.04, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "thin-participation" in str(row["note"])


def test_stablecoin_persistent_depeg_stays_zero() -> None:
    bars = _bars(AssetClass.STABLECOIN, close=1.0, step=0.0)
    depegged = bars[:-3] + [
        Candle("TEST", AssetClass.STABLECOIN, f"2026-01-01T{index:02d}:00:00Z", 0.99, 0.995, 0.985, 0.99, 100)
        for index in range(9, 12)
    ]
    row = apply_v12(depegged, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert row["side"] == "flat"
    assert "persistent-depeg" in str(row["note"])


def test_stablecoin_quiet_peg_stays_zero() -> None:
    row = apply_v12(_bars(AssetClass.STABLECOIN, close=1.0, step=0.0), proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "size stays zero" in str(row["note"])


def test_defi_inventory_unwind_veto() -> None:
    bars = _bars(AssetClass.DEFI, close=100.0, step=0.0)
    unwind = bars[:-4] + [
        Candle("TEST", AssetClass.DEFI, "2026-01-01T08:00:00Z", 100, 101, 99, 100, 100),
        Candle("TEST", AssetClass.DEFI, "2026-01-01T09:00:00Z", 104, 105, 103, 104, 100),
        Candle("TEST", AssetClass.DEFI, "2026-01-01T10:00:00Z", 108, 109, 107, 108, 100),
        Candle("TEST", AssetClass.DEFI, "2026-01-01T11:00:00Z", 112, 113, 111, 112, 100),
    ]
    row = apply_v12(unwind, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "inventory-unwind" in str(row["note"])


def test_meme_wash_print_veto() -> None:
    bars = _bars(AssetClass.MEME, volume=100.0)
    wash = bars[:-1] + [Candle("TEST", AssetClass.MEME, "2026-01-01T12:00:00Z", 100, 101, 99, 100.2, 2000)]
    row = apply_v12(wash, proposed_size=0.005, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "wash-print" in str(row["note"])


def test_l2_imbalance_haircut() -> None:
    bars = _bars(AssetClass.L2, volume=100.0)
    wide = bars[:-1] + [Candle("TEST", AssetClass.L2, "2026-01-01T12:00:00Z", 100, 108, 92, 100, 40)]
    row = apply_v12(wide, proposed_size=0.03, side=Side.LONG)
    assert row["size_fraction"] == 0.015
    assert "imbalance" in str(row["note"])


def test_rwa_unusual_print_veto() -> None:
    bars = _bars(AssetClass.RWA, volume=100.0)
    spike = bars[:-1] + [Candle("TEST", AssetClass.RWA, "2026-01-01T12:00:00Z", 101, 102, 100, 101, 800)]
    row = apply_v12(spike, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "unusual-print" in str(row["note"])


def test_perp_crowded_basis_haircut() -> None:
    bars = _bars(AssetClass.PERPETUAL, close=100.0, step=1.0, funding=0.001)
    row = apply_v12(bars, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.01
    assert "crowded-basis" in str(row["note"])


def test_perp_opposed_funding_keeps_size() -> None:
    bars = _bars(AssetClass.PERPETUAL, close=100.0, step=1.0, funding=-0.001)
    row = apply_v12(bars, proposed_size=0.02, side=Side.SHORT)
    assert row["size_fraction"] == 0.02
    assert "not triggered" in str(row["note"])


def test_flat_side_stays_zero() -> None:
    row = apply_v12(_bars(AssetClass.MAJOR, funding=0.0002), proposed_size=0.08, side=Side.FLAT)
    assert row["size_fraction"] == 0.0


def test_short_series_is_refused() -> None:
    with pytest.raises(ValueError, match="8 candles"):
        apply_v12(_bars(AssetClass.MAJOR)[:4], proposed_size=0.08, side=Side.LONG)


def test_desk_requires_synthetic_label_and_cannot_order() -> None:
    rows = [
        {"symbol": "BTC-USD", "asset_class": "major", "size_fraction": 0.04},
        {"symbol": "USDC-USD", "asset_class": "stablecoin", "size_fraction": 0.0},
    ]
    desk = information_desk(rows, fixture_label="SYNTHETIC")
    assert desk["order_instruction"] is False
    assert desk["can_increase_size"] is False
    assert desk["gross_paper_fraction"] == 0.04
    assert desk["lineage_digest"]
    with pytest.raises(ValueError, match="synthetic"):
        information_desk(rows, fixture_label="PRODUCTION")


def test_custody_plane_has_no_execution_zone() -> None:
    plane = custody_plane()
    assert plane["execution_zone"] is False
    assert plane["withdrawal_allowlist"] == []
    assert plane["withdrawal_allowlist_immutable"] is True
    assert plane["quorum"]["can_enable_live"] is False
    assert {item["zone"] for item in plane["zones"]} == {"research_hot", "research_warm", "research_cold"}
    assert all(item["can_trade"] is False for item in plane["zones"])
    operator = next(item for item in plane["separation_of_duties"] if item["role"] == "operator")
    assert operator["can_sign_digest"] is False
    assert operator["can_enable_live"] is False
    assert "private_key" in plane["data_plane"]["refused"]
    assert {item["domain"] for item in plane["trm_domains"]} == {
        "governance",
        "asset_management",
        "access_control",
        "cryptography",
        "data",
        "change_management",
        "incident",
        "cyber_hygiene",
    }
