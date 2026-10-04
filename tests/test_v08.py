import pytest

from crypto_intel.cli import main
from crypto_intel.desk import DESK_STAGES, build_dossier, correlation_shock, desk_manifest
from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.overlays import OVERLAY_NOTES, apply_overlay
from crypto_intel.zones import assert_zone_read, refuse_forbidden, seal, zone_catalog


def _series(
    symbol: str,
    asset_class: AssetClass,
    closes: list[float],
    *,
    volumes: list[float] | None = None,
    funding: list[float] | None = None,
) -> list[Candle]:
    rows = []
    for index, close in enumerate(closes):
        volume = 5000.0 if volumes is None else volumes[index]
        rate = 0.0 if funding is None else funding[index]
        rows.append(
            Candle(
                symbol,
                asset_class,
                f"2026-05-{index + 1:02d}T00:00:00Z",
                close,
                close * 1.01,
                close * 0.99,
                close,
                volume,
                rate,
            )
        )
    return rows


def test_desk_is_offline_and_shock_scales_paper_book():
    manifest = desk_manifest()
    assert manifest["version"] == "0.8.0"
    assert manifest["live_enabled"] is False
    assert manifest["order_path"] is False
    assert manifest["network_default"] is False
    assert tuple(manifest["stages"]) == DESK_STAGES
    falling = {
        "BTC-USD": _series("BTC-USD", AssetClass.MAJOR, [100, 100, 100, 90]),
        "ETH-USD": _series("ETH-USD", AssetClass.MAJOR, [100, 100, 100, 90]),
        "SOL-USD": _series("SOL-USD", AssetClass.LARGE_CAP_ALT, [100, 100, 100, 90]),
        "USDC-USD": _series("USDC-USD", AssetClass.STABLECOIN, [1, 1, 1, 1]),
    }
    shock = correlation_shock(falling)
    assert shock["active"] is True
    assert shock["paper_size_scale"] == 0.5
    assert "USDC-USD" not in shock["symbols"]
    calm = {"BTC-USD": _series("BTC-USD", AssetClass.MAJOR, [100, 101, 102, 103])}
    assert correlation_shock(calm)["active"] is False
    dossier = build_dossier(falling, label="SYNTHETIC", ages={"BTC-USD": 10}, zone_ok=True)
    assert dossier["paper_size_scale"] == 0.5
    assert dossier["live_enabled"] is False
    stale = build_dossier(calm, label="PUBLIC_READ", ages={"BTC-USD": 120}, zone_ok=True)
    assert stale["paper_size_scale"] == 0.0
    blocked = build_dossier(calm, label="SYNTHETIC", ages={}, zone_ok=False)
    assert blocked["paper_size_scale"] == 0.0
    with pytest.raises(ValueError):
        build_dossier(calm, label="customer", ages={}, zone_ok=True)
    with pytest.raises(ValueError):
        build_dossier({}, label="SYNTHETIC", ages={}, zone_ok=True)


def test_zones_refuse_secrets_and_do_not_authorize_live():
    catalog = zone_catalog()
    assert catalog["live_enabled"] is False
    assert catalog["order_path"] is False
    assert any(zone["zone"] == "forbidden" for zone in catalog["zones"])
    assert assert_zone_read("researcher", "public-market")["allowed"] is True
    assert assert_zone_read("auditor", "restricted-ops")["allowed"] is True
    with pytest.raises(PermissionError):
        assert_zone_read("researcher", "restricted-ops")
    with pytest.raises(PermissionError):
        assert_zone_read("operator", "forbidden")
    with pytest.raises(PermissionError):
        assert_zone_read("guest", "public-market")
    assert refuse_forbidden("symbol BTC-USD close 100")["accepted"] is True
    with pytest.raises(ValueError):
        refuse_forbidden("api_key=abc")
    with pytest.raises(ValueError):
        refuse_forbidden("user@example.com")
    with pytest.raises(ValueError):
        refuse_forbidden("0x" + "ab" * 20)
    sealed = seal("SYNTHETIC", "btc")
    assert sealed["digest"] == seal("SYNTHETIC", "btc")["digest"]
    assert sealed["authorizes_live"] is False
    with pytest.raises(ValueError):
        seal("LIVE", "btc")


def test_overlays_can_only_shrink_and_cover_each_class():
    assert set(OVERLAY_NOTES) == {item.value for item in AssetClass}
    weak = _series("BTC-USD", AssetClass.MAJOR, [100] * 8)
    weak[-1] = Candle("BTC-USD", AssetClass.MAJOR, weak[-1].timestamp, 100, 110, 90, 92, 5000, 0.0)
    major = apply_overlay(weak, proposed_size=0.08, side=Side.LONG)
    assert major["size_fraction"] == 0.04
    assert major["can_increase_size"] is False
    quiet = apply_overlay(
        _series("BTC-USD", AssetClass.MAJOR, [100 + i for i in range(8)]),
        proposed_size=0.08,
        side=Side.LONG,
    )
    assert quiet["size_fraction"] == 0.08

    wick = _series("SOL-USD", AssetClass.LARGE_CAP_ALT, [100] * 8)
    wick[-1] = Candle("SOL-USD", AssetClass.LARGE_CAP_ALT, wick[-1].timestamp, 100, 120, 99, 101, 5000, 0.0)
    assert apply_overlay(wick, proposed_size=0.04, side=Side.LONG)["size_fraction"] == 0.0

    stable = apply_overlay(
        _series("USDC-USD", AssetClass.STABLECOIN, [1.0, 1.0, 1.003, 1.003, 1.003, 1.003, 1.003, 1.003]),
        proposed_size=0.02,
        side=Side.LONG,
    )
    assert stable["size_fraction"] == 0.0
    assert "persistence" in str(stable["note"])

    defi = apply_overlay(
        _series("AAVE-USD", AssetClass.DEFI, [100] * 8, volumes=[1000, 1000, 1000, 1000, 1000, 1000, 1000, 100]),
        proposed_size=0.02,
        side=Side.LONG,
    )
    assert defi["size_fraction"] == 0.01

    meme = _series("PEPE-USD", AssetClass.MEME, [1] * 8)
    meme[-1] = Candle("PEPE-USD", AssetClass.MEME, meme[-1].timestamp, 1.0, 1.2, 0.99, 1.01, 5000, 0.0)
    assert apply_overlay(meme, proposed_size=0.005, side=Side.LONG)["size_fraction"] == 0.0

    bench = _series("ETH-USD", AssetClass.MAJOR, [100 * (1.02**i) for i in range(8)])
    lagging = _series("ARB-USD", AssetClass.L2, [100 - i for i in range(8)])
    assert apply_overlay(lagging, proposed_size=0.03, side=Side.LONG, benchmark=bench)["size_fraction"] == 0.0
    assert apply_overlay(lagging, proposed_size=0.03, side=Side.LONG)["size_fraction"] == 0.0

    rwa = _series("ONDO-USD", AssetClass.RWA, [50] * 8)
    rwa[-1] = Candle("ONDO-USD", AssetClass.RWA, rwa[-1].timestamp, 50, 54, 48, 53, 5000, 0.0)
    assert apply_overlay(rwa, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01

    perp = apply_overlay(
        _series("BTC-PERP", AssetClass.PERPETUAL, [100] * 8, funding=[0.0] * 7 + [0.002]),
        proposed_size=0.02,
        side=Side.SHORT,
    )
    assert perp["size_fraction"] == 0.0
    flat = apply_overlay(_series("BTC-USD", AssetClass.MAJOR, [100] * 8), proposed_size=0.08, side=Side.FLAT)
    assert flat["size_fraction"] == 0.0
    with pytest.raises(ValueError):
        apply_overlay(_series("BTC-USD", AssetClass.MAJOR, [100] * 4), proposed_size=0.01, side=Side.LONG)


def test_cli_v08_commands(capsys):
    assert main(["zones"]) == 0
    zones = capsys.readouterr().out
    assert "forbidden" in zones
    assert "0.8.0" in zones
    assert main(["desk", "fixtures/candles_synthetic.json"]) == 0
    desk = capsys.readouterr().out
    assert "paper_size_scale" in desk
    assert "live_enabled" in desk
    assert main(["overlay", "fixtures/candles_synthetic.json"]) == 0
    overlay = capsys.readouterr().out
    assert "can_increase_size" in overlay
    assert "false" in overlay.lower() or "False" in overlay
