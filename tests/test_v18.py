"""v0.18 participation guards, information console, and data-security plane."""

import pytest

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v18 import apply_v18, data_security_architecture, information_console, screen_record


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


def test_major_close_location_haircut_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR, close=100.0, step=0.0)
    weak = bars[:-1] + [
        Candle("TEST", AssetClass.MAJOR, "2026-01-01T11:00:00Z", 100, 104, 96, 97, 100),
    ]
    row = apply_v18(weak, proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.04
    assert row["can_increase_size"] is False
    assert row["order_path"] is False
    assert row["live_enabled"] is False
    assert "close-location" in str(row["note"])


def test_major_close_near_high_keeps_size() -> None:
    row = apply_v18(_bars(AssetClass.MAJOR), proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.08
    assert "not triggered" in str(row["note"])


def test_alt_climax_volume_haircut() -> None:
    bars = _bars(AssetClass.LARGE_CAP_ALT, close=100.0, step=0.0, volume=100.0)
    climax = bars[:-1] + [
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T11:00:00Z", 100, 101, 99, 100.4, 400),
    ]
    row = apply_v18(climax, proposed_size=0.04, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "climax-volume" in str(row["note"])


def test_stablecoin_peg_straddle_stays_zero() -> None:
    bars = _bars(AssetClass.STABLECOIN, close=1.0, step=0.0)
    straddled = bars[:-1] + [
        Candle("TEST", AssetClass.STABLECOIN, "2026-01-01T11:00:00Z", 1.0, 1.002, 0.998, 1.0, 100),
    ]
    row = apply_v18(straddled, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert row["side"] == "flat"
    assert "peg-band" in str(row["note"])


def test_stablecoin_quiet_peg_stays_zero() -> None:
    row = apply_v18(_bars(AssetClass.STABLECOIN, close=1.0, step=0.0), proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "size stays zero" in str(row["note"])


def test_defi_failed_break_haircut() -> None:
    bars = _bars(AssetClass.DEFI, close=100.0, step=0.0)
    failed = bars[:-1] + [
        Candle("TEST", AssetClass.DEFI, "2026-01-01T11:00:00Z", 100, 102, 99, 100.5, 100),
    ]
    row = apply_v18(failed, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.01
    assert "failed-break" in str(row["note"])


def test_meme_climax_veto() -> None:
    bars = _bars(AssetClass.MEME, close=100.0, step=0.0, volume=100.0)
    climax = bars[:-1] + [
        Candle("TEST", AssetClass.MEME, "2026-01-01T11:00:00Z", 100, 114, 98, 102, 400),
    ]
    row = apply_v18(climax, proposed_size=0.005, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "climax" in str(row["note"])


def test_l2_lag_haircut() -> None:
    bars = _bars(AssetClass.L2, close=100.0, step=0.0)
    lagged = bars[:-1] + [
        Candle("TEST", AssetClass.L2, "2026-01-01T11:00:00Z", 100, 101, 98, 99, 100),
    ]
    row = apply_v18(lagged, proposed_size=0.03, side=Side.LONG)
    assert row["size_fraction"] == 0.015
    assert "lag" in str(row["note"])


def test_rwa_identical_print_veto() -> None:
    bars = _bars(AssetClass.RWA, close=100.0, step=0.0)
    row = apply_v18(bars, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "identical-print" in str(row["note"])


def test_rwa_changing_print_keeps_size() -> None:
    row = apply_v18(_bars(AssetClass.RWA, close=100.0, step=0.2), proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "not triggered" in str(row["note"])


def test_perp_funding_flip_haircut() -> None:
    bars = _bars(AssetClass.PERPETUAL, close=100.0, step=0.1, funding=-0.0004)
    flipped = bars[:-1] + [
        Candle("TEST", AssetClass.PERPETUAL, "2026-01-01T11:00:00Z", 101, 102, 100, 101.2, 110, 0.0004),
    ]
    row = apply_v18(flipped, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.01
    assert "funding-flip" in str(row["note"])


def test_perp_stable_funding_keeps_size() -> None:
    row = apply_v18(_bars(AssetClass.PERPETUAL, funding=-0.0002), proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "not triggered" in str(row["note"])


def test_flat_side_stays_zero() -> None:
    row = apply_v18(_bars(AssetClass.MAJOR), proposed_size=0.08, side=Side.FLAT)
    assert row["size_fraction"] == 0.0


def test_short_series_is_refused() -> None:
    with pytest.raises(ValueError, match="8 candles"):
        apply_v18(_bars(AssetClass.MAJOR)[:4], proposed_size=0.08, side=Side.LONG)


def test_console_digest_is_not_an_order() -> None:
    rows = [
        {"symbol": "BTC-USD", "asset_class": "major", "size_fraction": 0.04, "side": "long", "note": "haircut"},
        {"symbol": "USDC-USD", "asset_class": "stablecoin", "size_fraction": 0.0, "side": "flat", "note": "watch"},
    ]
    packet = information_console(rows)
    again = information_console(rows)
    assert packet["network"] is False
    assert packet["order_instruction"] is False
    assert packet["can_enable_live"] is False
    assert packet["can_increase_size"] is False
    assert packet["flat_count"] == 1
    assert packet["haircut_count"] == 2
    assert packet["console_digest"] == again["console_digest"]
    assert packet["class_counts"]["major"] == 1
    assert all(stage["can_trade"] is False for stage in packet["stages"])


def test_record_screen_refuses_secret_and_wallet_fields() -> None:
    clean = screen_record({"symbol": "BTC-USD", "close": 100.0})
    secret = screen_record({"symbol": "BTC-USD", "api_key": "not-stored"})
    wallet = screen_record({"note": "pay 0x1111111111111111111111111111111111111111"})
    assert clean["accepted"] is True
    assert clean["can_trade"] is False
    assert secret["accepted"] is False
    assert secret["stored"] is False
    assert "api_key" in secret["blocked_fields"]
    assert wallet["accepted"] is False
    assert wallet["egress"] == "refused"


def test_data_security_plane_has_no_execution_zone() -> None:
    plane = data_security_architecture()
    assert plane["execution_zone"] is False
    assert plane["network"] is False
    assert plane["order_path"] is False
    classes = {item["field"]: item for item in plane["classes"]}
    assert classes["trade_or_withdrawal_key"]["retention"] == "zero"
    assert classes["wallet_address"]["egress"] == "refused"
    runner = next(item for item in plane["duties"] if item["identity"] == "automation_runner")
    assert runner["can_store_secret"] is False
    assert runner["can_enable_live"] is False
    operator = next(item for item in plane["duties"] if item["identity"] == "operator")
    assert operator["can_emit_console"] is False
    assert operator["can_trade"] is False
