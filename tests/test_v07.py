import pytest

from crypto_intel.automation import assemble_packet, evaluate_freshness, pipeline_manifest
from crypto_intel.cli import main
from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.sleeves import SLEEVE_NOTES, apply_sleeve
from crypto_intel.supply import (
    architecture_report,
    assert_break_glass,
    dependency_posture,
    fixture_integrity,
    role_allows,
)


def _series(
    symbol: str,
    asset_class: AssetClass,
    closes: list[float],
    *,
    volumes: list[float] | None = None,
    funding: list[float] | None = None,
    range_pct: float = 0.01,
    gap: float = 0.0,
) -> list[Candle]:
    rows = []
    for index, close in enumerate(closes):
        volume = 5000.0 if volumes is None else volumes[index]
        rate = 0.0 if funding is None else funding[index]
        open_px = close
        if index == len(closes) - 1 and index > 0:
            open_px = closes[index - 1] * (1 + gap)
        high = max(open_px, close) * (1 + range_pct)
        low = min(open_px, close) * (1 - range_pct)
        rows.append(
            Candle(
                symbol,
                asset_class,
                f"2026-04-{index + 1:02d}T00:00:00Z",
                open_px,
                high,
                low,
                close,
                volume,
                rate,
            )
        )
    return rows


def test_pipeline_manifest_is_offline_and_freshness_halts():
    manifest = pipeline_manifest()
    assert manifest["live_enabled"] is False
    assert manifest["order_path"] is False
    assert manifest["network_default"] is False
    assert evaluate_freshness("stablecoin", 30)["ok"] is True
    assert evaluate_freshness("stablecoin", 31)["ok"] is False
    with pytest.raises(ValueError):
        evaluate_freshness("unknown", 1)
    with pytest.raises(ValueError):
        evaluate_freshness("major", -1)
    notes = {stage: "ok" for stage in manifest["stages"]}
    packet = assemble_packet(label="SYNTHETIC", stage_notes=notes, freshness_ok=False)
    assert packet["paper_size_scale"] == 0.0
    assert packet["live_enabled"] is False
    with pytest.raises(ValueError):
        assemble_packet(label="customer", stage_notes=notes, freshness_ok=True)
    with pytest.raises(ValueError):
        assemble_packet(label="PUBLIC_READ", stage_notes={"ingest": "ok"}, freshness_ok=True)


def test_sleeves_can_only_shrink_and_cover_each_class():
    assert set(SLEEVE_NOTES) == {item.value for item in AssetClass}
    wide = _series("BTC-USD", AssetClass.MAJOR, [100] * 8, range_pct=0.01)
    wide[-1] = Candle(
        "BTC-USD",
        AssetClass.MAJOR,
        wide[-1].timestamp,
        100,
        130,
        70,
        100,
        5000,
        0.0,
    )
    major = apply_sleeve(wide, proposed_size=0.08, side=Side.LONG)
    assert major["size_fraction"] == 0.04
    assert major["can_increase_size"] is False

    bench = _series("BTC-USD", AssetClass.MAJOR, [100 * (1.02**i) for i in range(10)])
    lagging = _series("SOL-USD", AssetClass.LARGE_CAP_ALT, [100 - i for i in range(10)])
    alt = apply_sleeve(lagging, proposed_size=0.04, side=Side.LONG, benchmark=bench)
    assert alt["size_fraction"] == 0.0
    missing = apply_sleeve(lagging, proposed_size=0.04, side=Side.LONG)
    assert missing["size_fraction"] == 0.0

    stable = apply_sleeve(
        _series("USDC-USD", AssetClass.STABLECOIN, [1] * 8, range_pct=0.005),
        proposed_size=0.02,
        side=Side.LONG,
    )
    assert stable["size_fraction"] == 0.0
    assert "dispersion" in str(stable["note"])

    defi = apply_sleeve(
        _series("AAVE-USD", AssetClass.DEFI, [100] * 8, gap=0.08),
        proposed_size=0.02,
        side=Side.LONG,
    )
    assert defi["size_fraction"] == 0.0

    meme = apply_sleeve(
        _series("PEPE-USD", AssetClass.MEME, [1] * 8, volumes=[100, 100, 100, 400, 400, 400, 400, 10]),
        proposed_size=0.005,
        side=Side.LONG,
    )
    assert meme["size_fraction"] == 0.0025

    l2 = apply_sleeve(
        _series("ARB-USD", AssetClass.L2, [100] * 8, gap=0.06),
        proposed_size=0.03,
        side=Side.LONG,
    )
    assert l2["size_fraction"] == 0.0

    rwa = apply_sleeve(_series("ONDO-USD", AssetClass.RWA, [50] * 8), proposed_size=0.02, side=Side.LONG)
    assert rwa["size_fraction"] == 0.01

    funding = [0.001] * 7 + [-0.001]
    perp = apply_sleeve(
        _series("BTC-PERP", AssetClass.PERPETUAL, [100] * 8, funding=funding),
        proposed_size=0.02,
        side=Side.LONG,
    )
    assert perp["size_fraction"] == 0.0
    flat = apply_sleeve(_series("BTC-USD", AssetClass.MAJOR, [100] * 8), proposed_size=0.08, side=Side.FLAT)
    assert flat["size_fraction"] == 0.0
    quiet = apply_sleeve(
        _series("BTC-USD", AssetClass.MAJOR, [100 + i * 0.1 for i in range(8)]),
        proposed_size=0.08,
        side=Side.LONG,
    )
    assert quiet["size_fraction"] == 0.08
    leading = _series("SOL-USD", AssetClass.LARGE_CAP_ALT, [100 * (1.03**i) for i in range(10)])
    alt_ok = apply_sleeve(leading, proposed_size=0.04, side=Side.LONG, benchmark=bench)
    assert alt_ok["size_fraction"] == 0.04
    calm_stable = apply_sleeve(
        _series("USDC-USD", AssetClass.STABLECOIN, [1] * 8, range_pct=0.001),
        proposed_size=0.01,
        side=Side.ALERT,
    )
    assert calm_stable["size_fraction"] == 0.0
    defi_ok = apply_sleeve(
        _series("AAVE-USD", AssetClass.DEFI, [100 + i for i in range(8)]),
        proposed_size=0.02,
        side=Side.LONG,
    )
    assert defi_ok["size_fraction"] == 0.02
    meme_ok = apply_sleeve(
        _series("PEPE-USD", AssetClass.MEME, [1] * 8, volumes=[100] * 8),
        proposed_size=0.005,
        side=Side.LONG,
    )
    assert meme_ok["size_fraction"] == 0.005
    l2_ok = apply_sleeve(
        _series("ARB-USD", AssetClass.L2, [100 + i for i in range(8)]),
        proposed_size=0.03,
        side=Side.LONG,
    )
    assert l2_ok["size_fraction"] == 0.03
    rwa_ok = apply_sleeve(
        _series("ONDO-USD", AssetClass.RWA, [50 + i for i in range(8)]),
        proposed_size=0.02,
        side=Side.LONG,
    )
    assert rwa_ok["size_fraction"] == 0.02
    perp_ok = apply_sleeve(
        _series("BTC-PERP", AssetClass.PERPETUAL, [100] * 8, funding=[-0.001] * 8),
        proposed_size=0.02,
        side=Side.SHORT,
    )
    assert perp_ok["size_fraction"] == 0.02
    with pytest.raises(ValueError):
        apply_sleeve(_series("BTC-USD", AssetClass.MAJOR, [100] * 4), proposed_size=0.01, side=Side.LONG)


def test_supply_architecture_refuses_live_and_pii():
    posture = dependency_posture()
    assert posture["runtime_third_party"] == []
    assert posture["network_imports"] is False
    report = architecture_report()
    assert report["break_glass_can_enable_live"] is False
    assert all(row["pii"] is False for row in report["data_flow"])
    assert role_allows("operator", "kill_switch") is True
    assert role_allows("operator", "place_order") is False
    assert role_allows("researcher", "scan") is True
    with pytest.raises(PermissionError):
        role_allows("guest", "scan")
    with pytest.raises(PermissionError):
        assert_break_glass(requested_live=True)
    assert assert_break_glass(requested_live=False)["paper_only"] is True
    integrity = fixture_integrity("SYNTHETIC", '{"label": "SYNTHETIC"}')
    assert integrity["digest"] == fixture_integrity("SYNTHETIC", '{"label": "SYNTHETIC"}')["digest"]
    with pytest.raises(ValueError):
        fixture_integrity("LIVE", "SYNTHETIC")
    with pytest.raises(ValueError):
        fixture_integrity("SYNTHETIC", "unlabelled fixture")


def test_cli_v07_commands(capsys):
    assert main(["pipeline"]) == 0
    pipeline = capsys.readouterr().out
    assert "0.7.0" in pipeline
    assert main(["supply"]) == 0
    supply = capsys.readouterr().out
    assert "break_glass_can_enable_live" in supply
    assert main(["sleeve", "fixtures/candles_synthetic.json"]) == 0
    sleeve = capsys.readouterr().out
    assert "can_increase_size" in sleeve
    assert "live_enabled" in sleeve
