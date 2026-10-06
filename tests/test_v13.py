"""v0.13 event guards, information radar, and data-security plane."""

import pytest

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v13 import apply_v13, data_security_plane, information_radar


def _bars(
    asset_class: AssetClass,
    *,
    volume: float = 100.0,
    funding: float = 0.0,
    close: float = 100.0,
    step: float = 0.1,
    high_pad: float = 1.0,
    low_pad: float = 1.0,
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
                high=price + high_pad,
                low=price - low_pad,
                close=price,
                volume=volume + index,
                funding_rate=funding,
            )
        )
    return rows


def test_major_failed_auction_haircut_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR)
    bars[-1] = Candle("TEST", AssetClass.MAJOR, "2026-01-01T11:00:00Z", 102, 104, 100, 100.4, 120, 0.0)
    row = apply_v13(bars, proposed_size=0.04, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert row["can_increase_size"] is False
    assert "failed-auction" in str(row["note"])


def test_alt_follow_through_haircut() -> None:
    bars = _bars(AssetClass.LARGE_CAP_ALT)
    bars[-2] = Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T10:00:00Z", 100, 103, 99, 102, 110, 0.0)
    bars[-1] = Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T11:00:00Z", 102, 103, 99, 100, 110, 0.0)
    row = apply_v13(bars, proposed_size=0.04, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "failed-follow-through" in str(row["note"])


def test_stablecoin_velocity_stays_zero() -> None:
    bars = _bars(AssetClass.STABLECOIN, close=1.0, step=0.0)
    bars[-2] = Candle("TEST", AssetClass.STABLECOIN, "2026-01-01T10:00:00Z", 1.0, 1.002, 0.998, 1.001, 100, 0.0)
    bars[-1] = Candle("TEST", AssetClass.STABLECOIN, "2026-01-01T11:00:00Z", 1.001, 1.004, 0.998, 1.003, 100, 0.0)
    row = apply_v13(bars, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert row["side"] == "flat"
    assert "depeg-velocity" in str(row["note"])


def test_meme_exhaustion_wick_veto() -> None:
    bars = _bars(AssetClass.MEME)
    bars[-1] = Candle("TEST", AssetClass.MEME, "2026-01-01T11:00:00Z", 108, 120, 100, 104, 500, 0.0)
    row = apply_v13(bars, proposed_size=0.005, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "exhaustion-wick" in str(row["note"])


def test_perp_funding_acceleration_haircut() -> None:
    bars = _bars(AssetClass.PERPETUAL, funding=0.0001)
    bars[-3] = Candle("TEST", AssetClass.PERPETUAL, "2026-01-01T09:00:00Z", 100, 101, 99, 100, 100, 0.0002)
    bars[-2] = Candle("TEST", AssetClass.PERPETUAL, "2026-01-01T10:00:00Z", 100, 101, 99, 100, 100, 0.0003)
    bars[-1] = Candle("TEST", AssetClass.PERPETUAL, "2026-01-01T11:00:00Z", 100, 101, 99, 100, 100, 0.0005)
    row = apply_v13(bars, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.01
    assert "funding-acceleration" in str(row["note"])


def test_guard_cannot_raise_size() -> None:
    row = apply_v13(_bars(AssetClass.DEFI), proposed_size=0.01, side=Side.LONG)
    assert row["size_fraction"] <= 0.01
    assert row["order_path"] is False
    assert row["live_enabled"] is False


def test_radar_and_datasec_have_no_order_path() -> None:
    row = apply_v13(_bars(AssetClass.MAJOR), proposed_size=0.02, side=Side.LONG)
    radar = information_radar([row], fixture_label="SYNTHETIC")
    assert radar["order_instruction"] is False
    assert radar["purpose"] == "research_information"
    assert len(str(radar["lineage_digest"])) == 64
    plane = data_security_plane()
    assert plane["execution_zone"] is False
    assert plane["standing_privilege"] is False
    assert "trade_api_secret" in plane["data_classes_refused"]
    assert all(zone["can_trade"] is False for zone in plane["flow_zones"])
    with pytest.raises(ValueError):
        information_radar([row], fixture_label="LIVE")
