from datetime import datetime, timedelta, timezone

import pytest

from crypto_intel.cli import main
from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v09 import (
    GUARD_NOTES,
    acknowledge_change,
    apply_v09,
    research_cycle,
    route_alert,
    zero_trust_report,
)


def _series(
    symbol: str,
    asset_class: AssetClass,
    closes: list[float],
    *,
    volumes: list[float] | None = None,
    range_pct: float = 0.01,
    funding: float = 0.0,
    hours: int = 24,
) -> list[Candle]:
    rows = []
    start = datetime(2026, 5, 1, tzinfo=timezone.utc)
    for index, close in enumerate(closes):
        volume = 5000.0 if volumes is None else volumes[index]
        high = close * (1 + range_pct)
        low = close * (1 - range_pct)
        stamp = (start + timedelta(hours=hours * index)).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows.append(Candle(symbol, asset_class, stamp, close, high, low, close, volume, funding_rate=funding))
    return rows


def test_guards_cover_each_class_and_cannot_raise_size():
    assert set(GUARD_NOTES) == {item.value for item in AssetClass}
    falling = _series("BTC-USD", AssetClass.MAJOR, [110, 108, 106, 104, 102, 100, 98, 96])
    major = apply_v09(falling, proposed_size=0.08, side=Side.LONG)
    assert major["size_fraction"] == 0.04
    assert major["can_increase_size"] is False
    assert major["order_path"] is False
    quiet = apply_v09(_series("BTC-USD", AssetClass.MAJOR, [100] * 8), proposed_size=0.08, side=Side.LONG)
    assert quiet["size_fraction"] == 0.08

    alt = _series("SOL-USD", AssetClass.LARGE_CAP_ALT, [100] * 8)
    previous = alt[-2]
    alt[-1] = Candle(previous.symbol, previous.asset_class, alt[-1].timestamp, 108, 110, 100, 109, previous.volume)
    veto = apply_v09(alt, proposed_size=0.04, side=Side.LONG)
    assert veto["size_fraction"] == 0.0

    stable = apply_v09(_series("USDC-USD", AssetClass.STABLECOIN, [1.002] * 8), proposed_size=0.02, side=Side.LONG)
    assert stable["size_fraction"] == 0.0
    assert "peg" in str(stable["note"])

    wide = _series("AAVE-USD", AssetClass.DEFI, [100] * 8, range_pct=0.04)
    defi = apply_v09(wide, proposed_size=0.02, side=Side.LONG)
    assert defi["size_fraction"] == 0.0

    meme = apply_v09(
        _series("PEPE-USD", AssetClass.MEME, [1, 1, 1, 1, 1, 1.1, 1.2, 1.4]),
        proposed_size=0.005,
        side=Side.LONG,
    )
    assert meme["size_fraction"] == 0.0

    own = _series("ARB-USD", AssetClass.L2, [100, 100, 100, 100, 100, 100, 100, 100])
    bench = _series("ETH-USD", AssetClass.MAJOR, [100, 102, 104, 106, 108, 110, 112, 114])
    l2 = apply_v09(own, proposed_size=0.03, side=Side.LONG, benchmark=bench)
    assert l2["size_fraction"] == 0.015
    no_bench = apply_v09(own, proposed_size=0.03, side=Side.LONG)
    assert no_bench["size_fraction"] == 0.03

    stale = _series("ONDO-USD", AssetClass.RWA, [50] * 8, hours=48)
    rwa = apply_v09(stale, proposed_size=0.02, side=Side.LONG)
    assert rwa["size_fraction"] == 0.0
    fresh = apply_v09(_series("ONDO-USD", AssetClass.RWA, [50] * 8), proposed_size=0.02, side=Side.LONG)
    assert fresh["size_fraction"] == 0.02

    perp = apply_v09(
        _series("BTC-PERP", AssetClass.PERPETUAL, [100] * 8, funding=0.003),
        proposed_size=0.02,
        side=Side.SHORT,
    )
    assert perp["size_fraction"] == 0.0
    flat = apply_v09(_series("BTC-USD", AssetClass.MAJOR, [100] * 8), proposed_size=0.08, side=Side.FLAT)
    assert flat["size_fraction"] == 0.0
    with pytest.raises(ValueError):
        apply_v09(_series("BTC-USD", AssetClass.MAJOR, [100] * 4), proposed_size=0.01, side=Side.LONG)


def test_alerts_and_zero_trust_cannot_enable_live():
    halt = route_alert("stablecoin", deviation=0.006)
    assert halt["severity"] == "research_halt"
    assert halt["order_instruction"] is False
    watch = route_alert("meme", stress=True)
    assert watch["severity"] == "watch"
    info = route_alert("major")
    assert info["severity"] == "info"
    with pytest.raises(ValueError):
        route_alert("unknown")
    report = zero_trust_report()
    assert report["execution_zone"] is False
    assert report["live_enabled"] is False
    assert "protect" in {item["family"] for item in report["control_families"]}
    change = acknowledge_change("a" * 16, first="researcher", second="reviewer")
    assert change["can_enable_live"] is False
    assert change["order_path"] is False
    with pytest.raises(PermissionError):
        acknowledge_change("a" * 16, first="same", second="same")
    with pytest.raises(ValueError):
        acknowledge_change("short", first="a", second="b")
    cycle = research_cycle(
        [
            {"asset_class": "stablecoin", "deviation": 0.006},
            {"asset_class": "major", "stress": False},
            {"asset_class": "not-a-class"},
        ]
    )
    assert cycle["research_halt"] is True
    assert cycle["network_default"] is False
    assert cycle["order_path"] is False


def test_guard_edges_and_naive_timestamps():
    flat_alt = apply_v09(_series("SOL-USD", AssetClass.LARGE_CAP_ALT, [100] * 8), proposed_size=0.0, side=Side.FLAT)
    assert flat_alt["size_fraction"] == 0.0
    pegged = apply_v09(_series("USDC-USD", AssetClass.STABLECOIN, [1.0] * 8), proposed_size=0.0, side=Side.FLAT)
    assert "size stays zero" in str(pegged["note"])
    defi_flat = apply_v09(_series("AAVE-USD", AssetClass.DEFI, [100] * 8), proposed_size=0.0, side=Side.FLAT)
    assert defi_flat["size_fraction"] == 0.0
    meme_flat = apply_v09(_series("PEPE-USD", AssetClass.MEME, [1] * 8), proposed_size=0.0, side=Side.FLAT)
    assert meme_flat["size_fraction"] == 0.0
    own = _series("ARB-USD", AssetClass.L2, [100] * 8)
    dead = _series("ETH-USD", AssetClass.MAJOR, [0] * 8)
    lagged = apply_v09(own, proposed_size=0.03, side=Side.LONG, benchmark=dead)
    assert lagged["size_fraction"] == 0.03
    rwa_flat = apply_v09(_series("ONDO-USD", AssetClass.RWA, [50] * 8), proposed_size=0.0, side=Side.FLAT)
    assert rwa_flat["size_fraction"] == 0.0
    naive = _series("ONDO-USD", AssetClass.RWA, [50] * 8)
    naive[-2] = Candle(
        naive[-2].symbol,
        naive[-2].asset_class,
        "2026-05-07T00:00:00",
        50,
        51,
        49,
        50,
        5000,
    )
    naive[-1] = Candle(
        naive[-1].symbol,
        naive[-1].asset_class,
        "2026-05-08T00:00:00Z",
        50,
        51,
        49,
        50,
        5000,
    )
    fresh = apply_v09(naive, proposed_size=0.02, side=Side.LONG)
    assert fresh["size_fraction"] == 0.02
    tertiary = route_alert("stablecoin", deviation=0.0015)
    assert tertiary["severity"] == "watch"
    assert tertiary["order_instruction"] is False


def test_cli_information_commands(capsys):
    fixture = "fixtures/candles_synthetic.json"
    for command in (
        ["scan", fixture],
        ["demo", fixture],
        ["brief", fixture],
        ["posture", fixture],
        ["scorecard", fixture],
        ["controls"],
        ["intel", fixture],
        ["cross", fixture],
        ["threats"],
        ["walkforward", fixture, "--symbol", "BTC-USD"],
        ["enhance", fixture],
        ["cyber"],
        ["pipeline"],
        ["supply"],
        ["sleeve", fixture],
        ["backtest", fixture, "--symbol", "BTC-USD"],
    ):
        assert main(command) == 0
        assert capsys.readouterr().out
    with pytest.raises(SystemExit):
        main(["walkforward", fixture, "--symbol", "NO-SUCH"])
    with pytest.raises(SystemExit):
        main(["backtest", fixture, "--symbol", "NO-SUCH"])
    assert main(["zerotrust"]) == 0
    trust = capsys.readouterr().out
    assert "0.9.0" in trust
    assert "execution_zone" in trust
    assert main(["alerts", "fixtures/candles_synthetic.json"]) == 0
    alerts = capsys.readouterr().out
    assert "order_instruction" in alerts
    assert main(["v09", "fixtures/candles_synthetic.json"]) == 0
    guards = capsys.readouterr().out
    assert "can_increase_size" in guards
    assert "live_enabled" in guards
