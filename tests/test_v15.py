"""v0.15 concentration guards, information ledger, and segregation plane."""

import pytest

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v15 import apply_v15, information_ledger, segregation_plane


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


def test_major_open_gap_haircut_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR, close=100.0, step=0.0)
    gapped = bars[:-1] + [Candle("TEST", AssetClass.MAJOR, "2026-01-01T12:00:00Z", 102, 104, 101, 103.5, 100)]
    row = apply_v15(gapped, proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.04
    assert row["can_increase_size"] is False
    assert row["order_path"] is False
    assert row["live_enabled"] is False


def test_major_quiet_open_keeps_size() -> None:
    row = apply_v15(_bars(AssetClass.MAJOR), proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.08
    assert "not triggered" in str(row["note"])


def test_alt_failed_expansion_haircut() -> None:
    bars = _bars(AssetClass.LARGE_CAP_ALT, close=100.0, step=0.0)
    failed = bars[:-3] + [
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T09:00:00Z", 100, 101, 99, 100, 100),
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T10:00:00Z", 100, 102.5, 97.5, 101, 100),
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T11:00:00Z", 101, 106, 96, 100.5, 100),
    ]
    row = apply_v15(failed, proposed_size=0.04, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "failed-expansion" in str(row["note"])


def test_stablecoin_premium_watch_stays_zero() -> None:
    bars = _bars(AssetClass.STABLECOIN, close=1.0, step=0.0)
    premium = bars[:-1] + [
        Candle("TEST", AssetClass.STABLECOIN, "2026-01-01T12:00:00Z", 1.006, 1.008, 1.004, 1.007, 100)
    ]
    row = apply_v15(premium, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert row["side"] == "flat"
    assert "premium-persistence" in str(row["note"])


def test_stablecoin_quiet_peg_stays_zero() -> None:
    row = apply_v15(_bars(AssetClass.STABLECOIN, close=1.0, step=0.0), proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "size stays zero" in str(row["note"])


def test_defi_unlock_window_veto() -> None:
    bars = _bars(AssetClass.DEFI, close=100.0, step=0.0)
    unlocked = bars[:-3] + [
        Candle("TEST", AssetClass.DEFI, "2026-01-01T09:00:00Z", 103, 104, 102, 103, 100),
        Candle("TEST", AssetClass.DEFI, "2026-01-01T10:00:00Z", 102, 103.5, 100.5, 102, 100),
        Candle("TEST", AssetClass.DEFI, "2026-01-01T11:00:00Z", 101, 104, 98, 100, 100),
    ]
    row = apply_v15(unlocked, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "unlock-window" in str(row["note"])


def test_meme_climax_veto() -> None:
    bars = _bars(AssetClass.MEME, volume=100.0)
    climax = bars[:-1] + [Candle("TEST", AssetClass.MEME, "2026-01-01T12:00:00Z", 110, 112, 100, 102, 800)]
    row = apply_v15(climax, proposed_size=0.005, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "climax" in str(row["note"])


def test_l2_sequencer_stall_haircut() -> None:
    bars = _bars(AssetClass.L2, close=100.0, step=0.0)
    stalled = bars[:-3] + [
        Candle("TEST", AssetClass.L2, "2026-01-01T09:00:00Z", 100, 101, 99, 100, 300),
        Candle("TEST", AssetClass.L2, "2026-01-01T10:00:00Z", 100, 101, 99, 100, 200),
        Candle("TEST", AssetClass.L2, "2026-01-01T11:00:00Z", 100, 101, 99, 100, 100),
    ]
    row = apply_v15(stalled, proposed_size=0.03, side=Side.LONG)
    assert row["size_fraction"] == 0.015
    assert "sequencer-stall" in str(row["note"])


def test_rwa_oracle_gap_veto() -> None:
    bars = _bars(AssetClass.RWA, close=100.0, step=0.0)
    gapped = bars[:-1] + [Candle("TEST", AssetClass.RWA, "2026-01-01T12:00:00Z", 102, 103, 101, 102.2, 100)]
    row = apply_v15(gapped, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "oracle-gap" in str(row["note"])


def test_rwa_continuous_print_keeps_size() -> None:
    row = apply_v15(_bars(AssetClass.RWA, close=100.0, step=0.2), proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "not triggered" in str(row["note"])


def test_perp_crowded_expansion_haircut() -> None:
    bars = _bars(AssetClass.PERPETUAL, close=100.0, step=0.0, funding=0.0008)
    expanded = bars[:-3] + [
        Candle("TEST", AssetClass.PERPETUAL, "2026-01-01T09:00:00Z", 100, 101, 99, 100, 100, 0.0008),
        Candle("TEST", AssetClass.PERPETUAL, "2026-01-01T10:00:00Z", 100, 102, 98, 100, 100, 0.0008),
        Candle("TEST", AssetClass.PERPETUAL, "2026-01-01T11:00:00Z", 100, 103.5, 96.5, 100, 100, 0.0008),
    ]
    row = apply_v15(expanded, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.01
    assert "crowded-expansion" in str(row["note"])


def test_perp_quiet_funding_keeps_size() -> None:
    row = apply_v15(_bars(AssetClass.PERPETUAL, funding=0.0001), proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "not triggered" in str(row["note"])


def test_flat_side_stays_zero() -> None:
    row = apply_v15(_bars(AssetClass.MAJOR), proposed_size=0.08, side=Side.FLAT)
    assert row["size_fraction"] == 0.0


def test_short_series_is_refused() -> None:
    with pytest.raises(ValueError, match="8 candles"):
        apply_v15(_bars(AssetClass.MAJOR)[:4], proposed_size=0.08, side=Side.LONG)


def test_ledger_digest_is_not_an_order() -> None:
    packet = information_ledger(
        [
            {"symbol": "BTC-USD", "asset_class": "major", "size_fraction": 0.04, "side": "long", "note": "haircut"},
            {"symbol": "USDC-USD", "asset_class": "stablecoin", "size_fraction": 0.0, "side": "flat", "note": "watch"},
        ],
        previous_digest="abc",
    )
    again = information_ledger(
        [
            {"symbol": "BTC-USD", "asset_class": "major", "size_fraction": 0.04, "side": "long", "note": "haircut"},
            {"symbol": "USDC-USD", "asset_class": "stablecoin", "size_fraction": 0.0, "side": "flat", "note": "watch"},
        ],
        previous_digest="abc",
    )
    assert packet["network"] is False
    assert packet["order_instruction"] is False
    assert packet["can_enable_live"] is False
    assert packet["can_increase_size"] is False
    assert packet["flat_count"] == 1
    assert packet["ledger_digest"] == again["ledger_digest"]
    assert packet["previous_digest"] == "abc"
    assert all(stage["can_trade"] is False for stage in packet["stages"])


def test_segregation_plane_has_no_execution_zone() -> None:
    plane = segregation_plane()
    assert plane["execution_zone"] is False
    assert plane["segregation"]["dual_control_can_enable_live"] is False
    assert plane["segregation"]["automation_can_write_audit"] is False
    assert plane["automation"]["can_place_order"] is False
    assert plane["automation"]["can_open_socket"] is False
    runner = next(item for item in plane["duties"] if item["identity"] == "automation_runner")
    researcher = next(item for item in plane["duties"] if item["identity"] == "researcher")
    assert runner["can_read_research"] is False
    assert runner["can_enable_live"] is False
    assert researcher["can_append_audit"] is False
    assert "customer_wallet" in plane["data_classes"]["refused"]
    assert plane["data_classes"]["retention_personal_data"] == "zero"
