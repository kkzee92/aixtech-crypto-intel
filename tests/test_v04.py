from pathlib import Path

import pytest

from crypto_intel.confirm import confirm
from crypto_intel.custody import classify_name, clock_skew_ok, retention_days, rotation_status
from crypto_intel.intel import inform
from crypto_intel.market import group_by_symbol, load_candles
from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.quality import assess
from crypto_intel.sizing import vol_targeted_size
from crypto_intel.strategies import signal_for

FIXTURE = Path(__file__).parents[1] / "fixtures" / "candles_synthetic.json"


def test_quality_accepts_synthetic_fixture():
    grouped = group_by_symbol(load_candles(FIXTURE))
    report = assess(grouped["BTC-USD"])
    assert report.ok is True
    assert report.score == 1.0


def test_quality_flags_jump_and_duplicate():
    series = group_by_symbol(load_candles(FIXTURE))["BTC-USD"]
    jumped = list(series)
    last = jumped[-1]
    jumped[-1] = Candle(
        last.symbol,
        last.asset_class,
        last.timestamp,
        last.open,
        last.close * 1.5,
        last.low,
        last.close * 1.5,
        last.volume,
        last.funding_rate,
    )
    assert "jump_over_40pct" in assess(jumped).issues
    duplicated = list(series)
    duplicated[-1] = Candle(
        duplicated[-2].symbol,
        duplicated[-2].asset_class,
        duplicated[-2].timestamp,
        duplicated[-1].open,
        duplicated[-1].high,
        duplicated[-1].low,
        duplicated[-1].close,
        duplicated[-1].volume,
    )
    assert "duplicate_timestamp" in assess(duplicated).issues


def test_vol_target_never_raises_size_and_lst_is_tighter():
    series = group_by_symbol(load_candles(FIXTURE))["ETH-USD"]
    sized = vol_targeted_size(0.08, series, AssetClass.MAJOR)
    assert 0.0 < sized <= 0.08
    lst = [
        Candle(
            "stETH-LST",
            AssetClass.DEFI,
            candle.timestamp,
            candle.open,
            candle.high,
            candle.low,
            candle.close,
            candle.volume,
        )
        for candle in series
    ]
    assert vol_targeted_size(0.02, lst, AssetClass.DEFI) <= 0.01
    assert vol_targeted_size(0.02, series, AssetClass.STABLECOIN) == 0.0


def test_confirmation_vetoes_missing_l2_benchmark():
    grouped = group_by_symbol(load_candles(FIXTURE))
    series = grouped["ARB-USD"]
    signal = signal_for(series, benchmark=grouped["ETH-USD"])
    if signal.side is Side.LONG:
        allowed, reason = confirm(series, signal, benchmark=None)
        assert allowed is False
        assert "benchmark" in reason


def test_intel_report_is_paper_only():
    grouped = group_by_symbol(load_candles(FIXTURE))
    report = inform(grouped["BTC-USD"], benchmark=grouped["ETH-USD"])
    assert report["live_enabled"] is False
    assert report["mode"] == "paper"
    assert report["size_fraction"] <= 0.08
    assert report["quality_ok"] is True


def test_custody_policy():
    assert classify_name("market_read_key") == "read_market"
    with pytest.raises(PermissionError):
        classify_name("trade_api_key")
    with pytest.raises(PermissionError):
        classify_name("raw_secret")
    assert rotation_status(10, "read_market") == "current"
    assert rotation_status(100, "read_market") == "rotate"
    with pytest.raises(PermissionError):
        rotation_status(1, "trade")
    assert clock_skew_ok(30) is True
    assert clock_skew_ok(180) is False
    assert retention_days("secret") == 0
    assert retention_days("research_audit") == 365
