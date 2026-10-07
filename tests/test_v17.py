"""v0.17 event-window guards, information beacon, and identity plane."""

import pytest

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v17 import apply_v17, bind_session, identity_plane, information_beacon


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


def test_major_range_expansion_haircut_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR, close=100.0, step=0.0)
    quiet = bars[:-1]
    expanded = quiet + [
        Candle("TEST", AssetClass.MAJOR, "2026-01-01T11:00:00Z", 100, 106, 94, 101, 100),
    ]
    row = apply_v17(expanded, proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.04
    assert row["can_increase_size"] is False
    assert row["order_path"] is False
    assert row["live_enabled"] is False
    assert "range-expansion" in str(row["note"])


def test_major_quiet_path_keeps_size() -> None:
    row = apply_v17(_bars(AssetClass.MAJOR), proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.08
    assert "not triggered" in str(row["note"])


def test_alt_reversal_window_haircut() -> None:
    bars = _bars(AssetClass.LARGE_CAP_ALT, close=100.0, step=0.0)
    flipped = bars[:-3] + [
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T09:00:00Z", 100, 101, 99, 100, 100),
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T10:00:00Z", 100, 103, 99, 102, 100),
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T11:00:00Z", 102, 103, 99, 100, 100),
    ]
    row = apply_v17(flipped, proposed_size=0.04, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "reversal-window" in str(row["note"])


def test_stablecoin_wick_straddle_stays_zero() -> None:
    bars = _bars(AssetClass.STABLECOIN, close=1.0, step=0.0)
    straddled = bars[:-1] + [
        Candle("TEST", AssetClass.STABLECOIN, "2026-01-01T11:00:00Z", 1.0, 1.004, 0.996, 1.0, 100),
    ]
    row = apply_v17(straddled, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert row["side"] == "flat"
    assert "wick-straddle" in str(row["note"])


def test_stablecoin_quiet_peg_stays_zero() -> None:
    row = apply_v17(_bars(AssetClass.STABLECOIN, close=1.0, step=0.0), proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "size stays zero" in str(row["note"])


def test_defi_thin_tape_veto() -> None:
    bars = _bars(AssetClass.DEFI, close=100.0, step=0.0, volume=100.0)
    thin = bars[:-1] + [
        Candle("TEST", AssetClass.DEFI, "2026-01-01T11:00:00Z", 100, 103, 99, 103, 10),
    ]
    row = apply_v17(thin, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "thin-tape" in str(row["note"])


def test_meme_exhaustion_haircut() -> None:
    bars = _bars(AssetClass.MEME, close=100.0, step=0.0)
    exhausted = bars[:-3] + [
        Candle("TEST", AssetClass.MEME, "2026-01-01T09:00:00Z", 100, 101, 99.5, 100.4, 100),
        Candle("TEST", AssetClass.MEME, "2026-01-01T10:00:00Z", 100.4, 102, 99, 101, 100),
        Candle("TEST", AssetClass.MEME, "2026-01-01T11:00:00Z", 101, 104, 98, 100, 100),
    ]
    row = apply_v17(exhausted, proposed_size=0.005, side=Side.LONG)
    assert row["size_fraction"] == 0.0025
    assert "exhaustion" in str(row["note"])


def test_l2_reopen_gap_haircut() -> None:
    bars = _bars(AssetClass.L2, close=100.0, step=0.0, volume=100.0)
    gapped = bars[:-1] + [
        Candle("TEST", AssetClass.L2, "2026-01-01T11:00:00Z", 102, 103, 101, 102.4, 40),
    ]
    row = apply_v17(gapped, proposed_size=0.03, side=Side.LONG)
    assert row["size_fraction"] == 0.015
    assert "reopen-gap" in str(row["note"])


def test_rwa_auction_window_veto() -> None:
    bars = _bars(AssetClass.RWA, close=100.0, step=0.0)
    jumped = bars[:-2] + [
        Candle("TEST", AssetClass.RWA, "2026-01-01T10:00:00Z", 100.8, 101.2, 100.4, 101.0, 100),
        Candle("TEST", AssetClass.RWA, "2026-01-01T11:00:00Z", 101.8, 102.2, 101.4, 102.0, 100),
    ]
    row = apply_v17(jumped, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "auction-window" in str(row["note"])


def test_rwa_continuous_print_keeps_size() -> None:
    row = apply_v17(_bars(AssetClass.RWA, close=100.0, step=0.2), proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "not triggered" in str(row["note"])


def test_perp_inventory_skew_haircut() -> None:
    bars = _bars(AssetClass.PERPETUAL, close=100.0, step=0.0, funding=0.0008)
    wide = bars[:-1] + [
        Candle("TEST", AssetClass.PERPETUAL, "2026-01-01T11:00:00Z", 100, 102, 98, 100.4, 100, 0.0008),
    ]
    row = apply_v17(wide, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.01
    assert "inventory-skew" in str(row["note"])


def test_perp_calm_funding_keeps_size() -> None:
    row = apply_v17(_bars(AssetClass.PERPETUAL, funding=0.0001), proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "not triggered" in str(row["note"])


def test_flat_side_stays_zero() -> None:
    row = apply_v17(_bars(AssetClass.MAJOR), proposed_size=0.08, side=Side.FLAT)
    assert row["size_fraction"] == 0.0


def test_short_series_is_refused() -> None:
    with pytest.raises(ValueError, match="8 candles"):
        apply_v17(_bars(AssetClass.MAJOR)[:4], proposed_size=0.08, side=Side.LONG)


def test_beacon_digest_is_not_an_order() -> None:
    rows = [
        {"symbol": "BTC-USD", "asset_class": "major", "size_fraction": 0.04, "side": "long", "note": "haircut"},
        {"symbol": "USDC-USD", "asset_class": "stablecoin", "size_fraction": 0.0, "side": "flat", "note": "watch"},
    ]
    packet = information_beacon(rows)
    again = information_beacon(rows)
    assert packet["network"] is False
    assert packet["order_instruction"] is False
    assert packet["can_enable_live"] is False
    assert packet["can_increase_size"] is False
    assert packet["flat_count"] == 1
    assert packet["haircut_count"] == 2
    assert packet["beacon_digest"] == again["beacon_digest"]
    assert packet["class_counts"]["major"] == 1
    assert all(stage["can_trade"] is False for stage in packet["stages"])


def test_session_binding_refuses_trade_scope_and_role_reuse() -> None:
    bound = bind_session(role="researcher", scope="research_read")
    trade = bind_session(role="researcher", scope="trade")
    reused = bind_session(role="operator", scope="research_read", prior_role="researcher")
    assert bound["bound"] is True
    assert bound["can_emit_beacon"] is True
    assert bound["can_trade"] is False
    assert bound["standing_credential"] is False
    assert trade["bound"] is False
    assert trade["can_enable_live"] is False
    assert reused["bound"] is False
    assert reused["reusable_across_roles"] is False


def test_identity_plane_has_no_execution_zone() -> None:
    plane = identity_plane()
    assert plane["execution_zone"] is False
    assert plane["network"] is False
    assert plane["sessions"]["standing_credentials"] == "refused"
    assert "trade" in plane["sessions"]["refused_scopes"]
    runner = next(item for item in plane["duties"] if item["identity"] == "automation_runner")
    assert runner["can_mint_session"] is False
    assert runner["can_enable_live"] is False
    operator = next(item for item in plane["duties"] if item["identity"] == "operator")
    assert operator["can_emit_beacon"] is False
    assert operator["can_trade"] is False
