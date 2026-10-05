"""v0.12 microstructure guards, strategy cards, and lineage plane."""

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v12 import apply_v12, lineage_report, strategy_cards


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


def test_major_participation_haircut_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR, volume=100.0)
    thin = bars[:-1] + [Candle("TEST", AssetClass.MAJOR, "2026-01-01T12:00:00Z", 101, 102, 100, 101, 20)]
    row = apply_v12(thin, proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.04
    assert row["can_increase_size"] is False
    assert row["order_path"] is False
    assert row["live_enabled"] is False


def test_major_participation_keeps_size_when_volume_is_normal() -> None:
    row = apply_v12(_bars(AssetClass.MAJOR), proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.08
    assert "not triggered" in str(row["note"])


def test_alt_wick_rejection_veto() -> None:
    bars = _bars(AssetClass.LARGE_CAP_ALT, close=100.0, step=0.0)
    rejected = bars[:-1] + [Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T12:00:00Z", 104, 110, 100, 101, 120)]
    row = apply_v12(rejected, proposed_size=0.04, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "wick-rejection" in str(row["note"])


def test_stablecoin_secondary_peg_stays_zero() -> None:
    bars = _bars(AssetClass.STABLECOIN, close=1.0, step=0.0)
    soft = bars[:-1] + [Candle("TEST", AssetClass.STABLECOIN, "2026-01-01T12:00:00Z", 1.0, 1.002, 0.998, 0.998, 100)]
    row = apply_v12(soft, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert row["side"] == "flat"
    assert "peg" in str(row["note"])


def test_defi_impact_haircut() -> None:
    bars = _bars(AssetClass.DEFI, close=100.0, step=0.0, volume=100.0)
    impacted = bars[:-1] + [Candle("TEST", AssetClass.DEFI, "2026-01-01T12:00:00Z", 100, 104, 96, 100, 250)]
    row = apply_v12(impacted, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.01
    assert "impact haircut" in str(row["note"])


def test_meme_climax_veto() -> None:
    bars = _bars(AssetClass.MEME, close=100.0, step=0.0)
    climax = bars[:-1] + [Candle("TEST", AssetClass.MEME, "2026-01-01T12:00:00Z", 100, 114, 98, 100, 200)]
    row = apply_v12(climax, proposed_size=0.005, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "climax" in str(row["note"])


def test_l2_benchmark_lag_haircut() -> None:
    own = _bars(AssetClass.L2, close=100.0, step=0.0)
    bench = _bars(AssetClass.MAJOR, close=100.0, step=1.0)
    row = apply_v12(own, proposed_size=0.03, side=Side.LONG, benchmark=bench)
    assert row["size_fraction"] == 0.015
    assert "benchmark-lag" in str(row["note"])


def test_l2_without_benchmark_does_not_raise_size() -> None:
    row = apply_v12(_bars(AssetClass.L2), proposed_size=0.03, side=Side.LONG)
    assert row["size_fraction"] == 0.03
    assert "missing" in str(row["note"])


def test_rwa_thin_print_haircut() -> None:
    bars = _bars(AssetClass.RWA, volume=100.0)
    thin = bars[:-1] + [Candle("TEST", AssetClass.RWA, "2026-01-01T12:00:00Z", 101, 102, 100, 101, 30)]
    row = apply_v12(thin, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.01
    assert "thin-print" in str(row["note"])


def test_perp_basis_blowout_veto() -> None:
    bars = _bars(AssetClass.PERPETUAL, funding=0.0001)
    wide = bars[:-1] + [Candle("TEST", AssetClass.PERPETUAL, "2026-01-01T12:00:00Z", 100, 106, 94, 100, 120, 0.002)]
    row = apply_v12(wide, proposed_size=0.02, side=Side.SHORT)
    assert row["size_fraction"] == 0.0
    assert "basis-blowout" in str(row["note"])


def test_flat_side_stays_zero() -> None:
    row = apply_v12(_bars(AssetClass.MAJOR), proposed_size=0.08, side=Side.FLAT)
    assert row["size_fraction"] == 0.0


def test_cards_and_lineage_have_no_execution_zone() -> None:
    rows = [
        {"symbol": "BTC-USD", "asset_class": "major", "size_fraction": 0.04},
        {"symbol": "USDC-USD", "asset_class": "stablecoin", "size_fraction": 0.0},
    ]
    cards = strategy_cards(rows)
    assert cards["order_instruction"] is False
    assert cards["can_increase_size"] is False
    assert cards["gross_paper_fraction"] == 0.04
    assert cards["cards"][0]["guard"].startswith("participation")
    plane = lineage_report("SYNTHETIC", '{"label": "SYNTHETIC"}')
    assert plane["execution_zone"] is False
    assert plane["transport"]["keys_in_git"] is False
    assert plane["refused_secret_material"] is False
    assert {item["zone"] for item in plane["zones"]} == {"ingest", "research", "audit", "secrets"}
    assert all(item["can_trade"] is False for item in plane["zones"])
    dirty = lineage_report("SYNTHETIC", "api_key=should-not-be-here")
    assert dirty["refused_secret_material"] is True
    assert "api_key" not in dirty["fixture_digest"]
