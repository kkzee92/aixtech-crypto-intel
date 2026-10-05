"""v0.11 session guards, bulletin, and CSF plane."""

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v11 import apply_v11, csf_report, information_bulletin


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


def test_major_extension_haircut_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR, close=100.0, step=0.0)
    extended = bars[:-1] + [Candle("TEST", AssetClass.MAJOR, "2026-01-01T12:00:00Z", 110, 112, 109, 111, 120)]
    row = apply_v11(extended, proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.04
    assert row["can_increase_size"] is False
    assert row["order_path"] is False
    assert row["live_enabled"] is False


def test_major_quiet_series_keeps_proposed_size() -> None:
    row = apply_v11(_bars(AssetClass.MAJOR), proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.08
    assert "not triggered" in str(row["note"])


def test_alt_gap_haircut() -> None:
    bars = _bars(AssetClass.LARGE_CAP_ALT, close=100.0, step=0.0)
    gapped = bars[:-1] + [Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T12:00:00Z", 110, 112, 109, 111, 120)]
    row = apply_v11(gapped, proposed_size=0.04, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert "gap haircut" in str(row["note"])


def test_stablecoin_dispersion_stays_zero() -> None:
    bars = _bars(AssetClass.STABLECOIN, close=1.0, step=0.0)
    wide = bars[:-1] + [Candle("TEST", AssetClass.STABLECOIN, "2026-01-01T12:00:00Z", 1.0, 1.01, 0.99, 1.0, 100)]
    row = apply_v11(wide, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert row["side"] == "flat"
    assert "dispersion" in str(row["note"])


def test_defi_range_expansion_veto() -> None:
    bars = _bars(AssetClass.DEFI, close=100.0, step=0.0)
    expanded = bars[:-1] + [Candle("TEST", AssetClass.DEFI, "2026-01-01T12:00:00Z", 100, 106, 94, 101, 100)]
    row = apply_v11(expanded, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "range-expansion" in str(row["note"])


def test_meme_consecutive_gap_veto() -> None:
    bars = _bars(AssetClass.MEME, close=100.0, step=0.0)
    first = Candle("TEST", AssetClass.MEME, "2026-01-01T10:00:00Z", 112, 114, 111, 113, 100)
    second = Candle("TEST", AssetClass.MEME, "2026-01-01T11:00:00Z", 126, 128, 125, 127, 100)
    row = apply_v11(bars[:-2] + [first, second], proposed_size=0.005, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "consecutive-gap" in str(row["note"])


def test_l2_stuck_print_veto() -> None:
    bars = _bars(AssetClass.L2)
    stuck = bars[:-3] + [
        Candle("TEST", AssetClass.L2, f"2026-01-01T{index:02d}:00:00Z", 100, 101, 99, 100, 50) for index in range(9, 12)
    ]
    row = apply_v11(stuck, proposed_size=0.03, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "stuck-print" in str(row["note"])


def test_rwa_session_gap_veto() -> None:
    bars = _bars(AssetClass.RWA, close=100.0, step=0.0)
    gapped = bars[:-1] + [Candle("TEST", AssetClass.RWA, "2026-01-01T12:00:00Z", 106, 107, 105, 106.5, 80)]
    row = apply_v11(gapped, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "session-gap" in str(row["note"])


def test_perp_crowded_funding_veto() -> None:
    bars = _bars(AssetClass.PERPETUAL, volume=100.0, funding=0.0001)
    crowded = bars[:-1] + [Candle("TEST", AssetClass.PERPETUAL, "2026-01-01T12:00:00Z", 101, 102, 100, 101, 400, 0.002)]
    row = apply_v11(crowded, proposed_size=0.02, side=Side.SHORT)
    assert row["size_fraction"] == 0.0
    assert "crowded-funding" in str(row["note"])


def test_flat_side_stays_zero() -> None:
    row = apply_v11(_bars(AssetClass.MAJOR), proposed_size=0.08, side=Side.FLAT)
    assert row["size_fraction"] == 0.0


def test_bulletin_and_csf_have_no_execution_zone() -> None:
    rows = [
        {"symbol": "BTC-USD", "asset_class": "major", "size_fraction": 0.04},
        {"symbol": "USDC-USD", "asset_class": "stablecoin", "size_fraction": 0.0},
    ]
    bulletin = information_bulletin(rows)
    assert bulletin["order_instruction"] is False
    assert bulletin["can_increase_size"] is False
    assert bulletin["gross_paper_fraction"] == 0.04
    assert bulletin["class_counts"]["major"] == 1
    plane = csf_report()
    assert plane["execution_zone"] is False
    assert {item["function"] for item in plane["functions"]} == {
        "govern",
        "identify",
        "protect",
        "detect",
        "respond",
        "recover",
    }
    duties = plane["separation_of_duties"]
    assert all(item["can_trade"] is False and item["can_enable_live"] is False for item in duties)
    assert "credential" in plane["data_plane"]["refused"]
