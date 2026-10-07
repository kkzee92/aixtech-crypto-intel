"""v0.16 correlation-break guards, information radar, and DLP egress plane."""

import pytest

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v16 import apply_v16, dlp_plane, information_radar, scan_egress


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


def test_major_whipsaw_haircut_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR, close=100.0, step=0.0)
    prices = [100.0, 101.0, 100.2, 101.2, 100.3]
    whipsaw = bars[:-5]
    for index, price in enumerate(prices):
        previous = prices[index - 1] if index else 100.0
        whipsaw.append(
            Candle(
                "TEST",
                AssetClass.MAJOR,
                f"2026-01-01T{7 + index:02d}:00:00Z",
                previous,
                max(previous, price) + 0.2,
                min(previous, price) - 0.2,
                price,
                100,
            )
        )
    row = apply_v16(whipsaw, proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.04
    assert row["can_increase_size"] is False
    assert row["order_path"] is False
    assert row["live_enabled"] is False
    assert "whipsaw" in str(row["note"])


def test_major_quiet_path_keeps_size() -> None:
    row = apply_v16(_bars(AssetClass.MAJOR), proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.08
    assert "not triggered" in str(row["note"])


def test_alt_volume_divergence_haircut() -> None:
    bars = _bars(AssetClass.LARGE_CAP_ALT, close=100.0, step=0.0)
    diverged = bars[:-4] + [
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T08:00:00Z", 100, 101, 99, 100, 400),
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T09:00:00Z", 100, 102, 99, 101, 300),
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T10:00:00Z", 101, 103, 100, 102, 200),
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T11:00:00Z", 102, 104, 101, 103, 100),
    ]
    row = apply_v16(diverged, proposed_size=0.04, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "volume-divergence" in str(row["note"])


def test_stablecoin_peg_persistence_stays_zero() -> None:
    bars = _bars(AssetClass.STABLECOIN, close=1.003, step=0.0)
    row = apply_v16(bars, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert row["side"] == "flat"
    assert "peg-persistence" in str(row["note"])


def test_stablecoin_quiet_peg_stays_zero() -> None:
    row = apply_v16(_bars(AssetClass.STABLECOIN, close=1.0, step=0.0), proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "size stays zero" in str(row["note"])


def test_defi_cascade_veto() -> None:
    bars = _bars(AssetClass.DEFI, close=100.0, step=0.0)
    cascaded = bars[:-4]
    price = 100.0
    for index in range(4):
        nxt = price * 1.05
        cascaded.append(
            Candle(
                "TEST",
                AssetClass.DEFI,
                f"2026-01-01T{8 + index:02d}:00:00Z",
                price,
                nxt + 0.2,
                price - 0.2,
                nxt,
                100,
            )
        )
        price = nxt
    row = apply_v16(cascaded, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "cascade" in str(row["note"])


def test_meme_participation_break_haircut() -> None:
    bars = _bars(AssetClass.MEME, close=100.0, step=0.0)
    faded = bars[:-4] + [
        Candle("TEST", AssetClass.MEME, "2026-01-01T08:00:00Z", 100, 101, 99, 100, 400),
        Candle("TEST", AssetClass.MEME, "2026-01-01T09:00:00Z", 100, 102, 99, 101, 300),
        Candle("TEST", AssetClass.MEME, "2026-01-01T10:00:00Z", 101, 103, 100, 102, 200),
        Candle("TEST", AssetClass.MEME, "2026-01-01T11:00:00Z", 102, 104, 101, 103, 100),
    ]
    row = apply_v16(faded, proposed_size=0.005, side=Side.LONG)
    assert row["size_fraction"] == 0.0025
    assert "participation-break" in str(row["note"])


def test_l2_path_break_haircut() -> None:
    bars = _bars(AssetClass.L2, close=100.0, step=0.0)
    broken = bars[:-6] + [
        Candle("TEST", AssetClass.L2, "2026-01-01T06:00:00Z", 100, 101, 99, 100, 100),
        Candle("TEST", AssetClass.L2, "2026-01-01T07:00:00Z", 100, 104, 99, 103, 100),
        Candle("TEST", AssetClass.L2, "2026-01-01T08:00:00Z", 103, 108, 102, 107, 100),
        Candle("TEST", AssetClass.L2, "2026-01-01T09:00:00Z", 107, 112, 106, 110, 100),
        Candle("TEST", AssetClass.L2, "2026-01-01T10:00:00Z", 110, 111, 106, 107, 100),
        Candle("TEST", AssetClass.L2, "2026-01-01T11:00:00Z", 107, 108, 103, 104, 100),
    ]
    row = apply_v16(broken, proposed_size=0.03, side=Side.LONG)
    assert row["size_fraction"] == 0.015
    assert "path-break" in str(row["note"])


def test_rwa_jump_cluster_veto() -> None:
    bars = _bars(AssetClass.RWA, close=100.0, step=0.0)
    jumped = bars[:-3] + [
        Candle("TEST", AssetClass.RWA, "2026-01-01T09:00:00Z", 100.6, 101.2, 100.2, 100.8, 100),
        Candle("TEST", AssetClass.RWA, "2026-01-01T10:00:00Z", 101.4, 102.0, 101.0, 101.6, 100),
        Candle("TEST", AssetClass.RWA, "2026-01-01T11:00:00Z", 102.2, 102.8, 101.8, 102.4, 100),
    ]
    row = apply_v16(jumped, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "jump-cluster" in str(row["note"])


def test_rwa_continuous_print_keeps_size() -> None:
    row = apply_v16(_bars(AssetClass.RWA, close=100.0, step=0.2), proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "not triggered" in str(row["note"])


def test_perp_funding_divergence_haircut() -> None:
    bars = _bars(AssetClass.PERPETUAL, close=100.0, step=0.6, funding=-0.0008)
    row = apply_v16(bars, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.01
    assert "funding-divergence" in str(row["note"])


def test_perp_aligned_funding_keeps_size() -> None:
    row = apply_v16(_bars(AssetClass.PERPETUAL, funding=0.0001), proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "not triggered" in str(row["note"])


def test_flat_side_stays_zero() -> None:
    row = apply_v16(_bars(AssetClass.MAJOR), proposed_size=0.08, side=Side.FLAT)
    assert row["size_fraction"] == 0.0


def test_short_series_is_refused() -> None:
    with pytest.raises(ValueError, match="8 candles"):
        apply_v16(_bars(AssetClass.MAJOR)[:4], proposed_size=0.08, side=Side.LONG)


def test_radar_digest_is_not_an_order() -> None:
    rows = [
        {"symbol": "BTC-USD", "asset_class": "major", "size_fraction": 0.04, "side": "long", "note": "haircut"},
        {"symbol": "USDC-USD", "asset_class": "stablecoin", "size_fraction": 0.0, "side": "flat", "note": "watch"},
    ]
    packet = information_radar(rows)
    again = information_radar(rows)
    assert packet["network"] is False
    assert packet["order_instruction"] is False
    assert packet["can_enable_live"] is False
    assert packet["can_increase_size"] is False
    assert packet["flat_count"] == 1
    assert packet["haircut_count"] == 2
    assert packet["radar_digest"] == again["radar_digest"]
    assert packet["class_counts"]["major"] == 1
    assert all(stage["can_trade"] is False for stage in packet["stages"])


def test_dlp_blocks_secret_wallet_and_email() -> None:
    clean = scan_egress("major size_fraction=0.04 note=whipsaw")
    dirty = scan_egress("api_key=abcd1234efgh wallet 0x" + "ab" * 20 + " user@example.com +6591234567")
    assert clean["allowed"] is True
    assert clean["destination"] == "research_digest"
    assert dirty["allowed"] is False
    assert dirty["destination"] == "blocked"
    assert set(dirty["findings"]) == {"secret", "wallet", "email", "phone"}
    assert dirty["can_enable_live"] is False


def test_dlp_plane_has_no_execution_zone() -> None:
    plane = dlp_plane()
    assert plane["execution_zone"] is False
    assert plane["network"] is False
    assert plane["egress"]["retention_personal_data"] == "zero"
    assert "exchange_order" in plane["egress"]["refused_destinations"]
    assert "wallet_address" in plane["egress"]["refused_payloads"]
    runner = next(item for item in plane["duties"] if item["identity"] == "automation_runner")
    assert runner["can_emit_digest"] is False
    assert runner["can_enable_live"] is False
