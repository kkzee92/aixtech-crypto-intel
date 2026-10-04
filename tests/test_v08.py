import pytest

from crypto_intel.cli import main
from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v08 import (
    CADENCE_MINUTES,
    OVERLAY_NOTES,
    apply_v08,
    assert_data_class,
    data_plane_report,
    export_envelope,
    next_window,
    schedule_manifest,
)


def _series(
    symbol: str,
    asset_class: AssetClass,
    closes: list[float],
    *,
    volumes: list[float] | None = None,
    range_pct: float = 0.01,
) -> list[Candle]:
    rows = []
    for index, close in enumerate(closes):
        volume = 5000.0 if volumes is None else volumes[index]
        high = close * (1 + range_pct)
        low = close * (1 - range_pct)
        rows.append(Candle(symbol, asset_class, f"2026-05-{index + 1:02d}T00:00:00Z", close, high, low, close, volume))
    return rows


def test_overlays_cover_each_class_and_cannot_raise_size():
    assert set(OVERLAY_NOTES) == {item.value for item in AssetClass}
    thin = _series("BTC-USD", AssetClass.MAJOR, [100] * 8, volumes=[1000] * 7 + [100])
    major = apply_v08(thin, proposed_size=0.08, side=Side.LONG)
    assert major["size_fraction"] == 0.04
    assert major["can_increase_size"] is False
    assert major["order_path"] is False

    alt_candles = _series("SOL-USD", AssetClass.LARGE_CAP_ALT, [100] * 8)
    last = alt_candles[-1]
    alt_candles[-1] = Candle(last.symbol, last.asset_class, last.timestamp, 100, 110, 90, 92, last.volume)
    alt = apply_v08(alt_candles, proposed_size=0.04, side=Side.LONG)
    assert alt["size_fraction"] == 0.02

    stable = apply_v08(_series("USDC-USD", AssetClass.STABLECOIN, [1.003] * 8), proposed_size=0.02, side=Side.LONG)
    assert stable["size_fraction"] == 0.0
    assert "peg" in str(stable["note"])

    defi = apply_v08(
        _series("AAVE-USD", AssetClass.DEFI, [100] * 8, volumes=[1000] * 7 + [100]),
        proposed_size=0.02,
        side=Side.LONG,
    )
    assert defi["size_fraction"] == 0.0

    meme_candles = _series("PEPE-USD", AssetClass.MEME, [1] * 8)
    meme_last = meme_candles[-1]
    meme_candles[-1] = Candle(meme_last.symbol, meme_last.asset_class, meme_last.timestamp, 1.0, 1.2, 0.95, 1.0, 5000)
    meme = apply_v08(meme_candles, proposed_size=0.005, side=Side.LONG)
    assert meme["size_fraction"] == 0.0

    l2_candles = _series("ARB-USD", AssetClass.L2, [100] * 8, range_pct=0.01)
    l2_last = l2_candles[-1]
    l2_candles[-1] = Candle(l2_last.symbol, l2_last.asset_class, l2_last.timestamp, 100, 140, 60, 100, 5000)
    l2 = apply_v08(l2_candles, proposed_size=0.03, side=Side.LONG)
    assert l2["size_fraction"] == 0.015

    rwa = apply_v08(_series("ONDO-USD", AssetClass.RWA, [50] * 8), proposed_size=0.02, side=Side.LONG)
    assert rwa["size_fraction"] == 0.0
    rwa_up = apply_v08(
        _series("ONDO-USD", AssetClass.RWA, [50 + i for i in range(8)]),
        proposed_size=0.02,
        side=Side.LONG,
    )
    assert rwa_up["size_fraction"] == 0.02

    perp = apply_v08(
        _series("BTC-PERP", AssetClass.PERPETUAL, [100] * 8, volumes=[100] * 7 + [1000]),
        proposed_size=0.02,
        side=Side.SHORT,
    )
    assert perp["size_fraction"] == 0.01
    flat = apply_v08(_series("BTC-USD", AssetClass.MAJOR, [100] * 8), proposed_size=0.08, side=Side.FLAT)
    assert flat["size_fraction"] == 0.0
    quiet = apply_v08(_series("BTC-USD", AssetClass.MAJOR, [100] * 8), proposed_size=0.08, side=Side.LONG)
    assert quiet["size_fraction"] == 0.08
    with pytest.raises(ValueError):
        apply_v08(_series("BTC-USD", AssetClass.MAJOR, [100] * 4), proposed_size=0.01, side=Side.LONG)


def test_schedule_and_data_plane_stay_offline():
    manifest = schedule_manifest()
    assert manifest["live_enabled"] is False
    assert manifest["order_path"] is False
    assert set(manifest["cadence_minutes"]) == set(CADENCE_MINUTES)
    window = next_window("2026-10-04T09:07:00Z", "stablecoin")
    assert window["next_iso"] == "2026-10-04T09:10:00Z"
    assert window["order_path"] is False
    with pytest.raises(ValueError):
        next_window("2026-10-04T09:07:00Z", "unknown")
    report = data_plane_report()
    assert report["execution_zone"] is False
    assert report["order_path"] is False
    assert "wallet_seed" in report["refused_classes"]
    assert assert_data_class("public_market") == "public_market"
    with pytest.raises(PermissionError):
        assert_data_class("wallet_seed")
    with pytest.raises(PermissionError):
        assert_data_class("customer_email")
    envelope = export_envelope("SYNTHETIC", "body")
    assert envelope["digest"] == export_envelope("SYNTHETIC", "body")["digest"]
    assert envelope["live_enabled"] is False
    with pytest.raises(ValueError):
        export_envelope("LIVE", "body")


def test_cli_v08_commands(capsys):
    assert main(["schedule"]) == 0
    schedule = capsys.readouterr().out
    assert "0.8.0" in schedule
    assert "order_path" in schedule
    assert main(["dataplane"]) == 0
    plane = capsys.readouterr().out
    assert "execution_zone" in plane
    assert main(["v08", "fixtures/candles_synthetic.json"]) == 0
    overlay = capsys.readouterr().out
    assert "can_increase_size" in overlay
    assert "live_enabled" in overlay
