from pathlib import Path

import pytest

from crypto_intel.book import GROSS_CAP, allocate
from crypto_intel.catalog import SPECS, parameter_digest
from crypto_intel.controls import DualControl, assert_read_only_endpoint, control_report
from crypto_intel.market import group_by_symbol, load_candles
from crypto_intel.models import AssetClass, Side
from crypto_intel.posture import Role
from crypto_intel.risk import evaluate
from crypto_intel.scorecard import score_book
from crypto_intel.strategies import signal_for

FIXTURE = Path(__file__).parents[1] / "fixtures" / "candles_synthetic.json"


def test_catalog_covers_classes_and_is_stable():
    assert set(SPECS) == set(AssetClass)
    digest = parameter_digest()
    assert len(digest) == 64
    assert digest == parameter_digest()
    assert SPECS[AssetClass.STABLECOIN]["size_cap"] == 0.0
    assert SPECS[AssetClass.PERPETUAL]["short_cap"] < SPECS[AssetClass.PERPETUAL]["size_cap"]


def test_book_scales_gross_exposure():
    grouped = group_by_symbol(load_candles(FIXTURE))
    proposals = []
    for symbol, series in grouped.items():
        signal = signal_for(series, benchmark=grouped.get("ETH-USD"))
        decision = evaluate(signal)
        proposals.append((signal, decision.size_fraction))
    rows = allocate(proposals)
    assert sum(row.allocated for row in rows) <= GROSS_CAP + 1e-9
    assert all(row.allocated <= row.proposed + 1e-9 for row in rows)
    assert all(row.allocated == 0.0 for row in rows if row.asset_class is AssetClass.STABLECOIN)


def test_scorecard_is_labelled_synthetic():
    grouped = group_by_symbol(load_candles(FIXTURE))
    card = score_book(grouped)
    assert card["fixture"] == "synthetic"
    assert card["mode"] == "paper"
    assert {row["asset_class"] for row in card["classes"]} <= {item.value for item in AssetClass}
    assert all(row["ending_equity"] > 0 for row in card["rows"])


def test_dual_control_and_egress():
    switch = DualControl()
    with pytest.raises(PermissionError):
        switch.engage(Role.RESEARCHER)
    switch.engage(Role.OPERATOR)
    assert switch.engaged is True
    with pytest.raises(PermissionError):
        switch.confirm_clear(Role.AUDITOR)
    switch.request_clear(Role.OPERATOR)
    with pytest.raises(PermissionError):
        switch.confirm_clear(Role.OPERATOR)
    switch.confirm_clear(Role.AUDITOR)
    assert switch.engaged is False
    assert_read_only_endpoint("https://api.coingecko.com/api/v3/simple/price")
    with pytest.raises(PermissionError):
        assert_read_only_endpoint("http://api.coingecko.com/api/v3/simple/price")
    with pytest.raises(PermissionError):
        assert_read_only_endpoint("https://evil.example/ticker")
    with pytest.raises(PermissionError):
        assert_read_only_endpoint("https://api.binance.com/api/v3/order")
    report = control_report()
    assert report["live_enabled"] is False
    assert report["parameter_digest"] == parameter_digest()
    assert any(item["id"] == "RS.MI-1" for item in report["controls"])


def test_perpetual_short_is_class_limited():
    grouped = group_by_symbol(load_candles(FIXTURE))
    series = grouped["BTC-PERP"]
    crowded = []
    for candle in series:
        crowded.append(
            type(candle)(
                candle.symbol,
                candle.asset_class,
                candle.timestamp,
                candle.open,
                candle.high,
                candle.low,
                candle.close,
                candle.volume,
                0.002,
            )
        )
    # Force a positive drift so the crowded-funding fade can qualify.
    last = crowded[-1]
    earlier = crowded[-6]
    if last.close / earlier.close - 1.0 <= 0.04:
        bumped = type(last)(
            last.symbol,
            last.asset_class,
            last.timestamp,
            earlier.close * 1.05,
            earlier.close * 1.08,
            earlier.close * 1.04,
            earlier.close * 1.06,
            last.volume,
            0.002,
        )
        crowded[-1] = bumped
    signal = signal_for(crowded)
    assert signal.side is Side.SHORT
    decision = evaluate(signal)
    assert decision.allowed is True
    assert decision.size_fraction <= 0.01
