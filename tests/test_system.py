from pathlib import Path

import pytest

from crypto_intel.engine import backtest, run_once
from crypto_intel.market import fetch_public_ticker, group_by_symbol, load_candles
from crypto_intel.models import AssetClass, Candle, ExecutionMode, Side
from crypto_intel.risk import evaluate
from crypto_intel.security import AuditLog, assert_paper_only, contains_secret, redact
from crypto_intel.strategies import signal_for

FIXTURE = Path(__file__).parents[1] / "fixtures" / "candles_synthetic.json"


def test_load_and_group():
    grouped = group_by_symbol(load_candles(FIXTURE))
    assert "BTC-USD" in grouped
    assert grouped["BTC-USD"][0].asset_class is AssetClass.MAJOR


def test_public_ticker_is_injected():
    seen = {}

    def fetcher(symbol: str) -> dict:
        seen["symbol"] = symbol
        return {"price": 10, "volume": 3}

    parsed = fetch_public_ticker("BTC-USD", fetcher)
    assert seen["symbol"] == "BTC-USD"
    assert parsed["price"] == 10


def test_secret_redaction_and_audit_chain():
    raw = "api_key=abcdefghijklmno wallet 0x1234567890abcdef1234567890abcdef12345678"
    assert contains_secret(raw)
    assert "[REDACTED]" in redact(raw)
    assert "[WALLET]" in redact(raw)
    log = AuditLog()
    log.append("note", raw)
    assert log.verify()
    log.events[0].detail = "tampered"
    assert not log.verify()


def test_live_mode_refused():
    with pytest.raises(PermissionError):
        assert_paper_only(ExecutionMode.HALTED)


def test_each_asset_class_has_a_signal():
    grouped = group_by_symbol(load_candles(FIXTURE))
    for series in grouped.values():
        signal = signal_for(series, benchmark=grouped["ETH-USD"])
        assert signal.symbol == series[-1].symbol
        assert 0 <= signal.confidence <= 1


def test_stablecoin_cannot_take_risk():
    grouped = group_by_symbol(load_candles(FIXTURE))
    signal = signal_for(grouped["USDC-USD"])
    decision = evaluate(signal)
    assert signal.side is Side.ALERT
    assert decision.allowed is False


def test_kill_switch_blocks_major():
    grouped = group_by_symbol(load_candles(FIXTURE))
    signal, fill = run_once(grouped["BTC-USD"], audit=AuditLog(), kill_switch=True)
    assert signal.symbol == "BTC-USD"
    assert fill.size_fraction == 0.0
    assert "kill switch" in fill.reason


def test_backtest_is_paper_and_finite():
    grouped = group_by_symbol(load_candles(FIXTURE))
    result = backtest(grouped["BTC-USD"])
    assert result["ending_equity"] > 0
    assert result["trades"] >= 0


def test_drawdown_and_rwa_gap_halt():
    grouped = group_by_symbol(load_candles(FIXTURE))
    signal = signal_for(grouped["ONDO-USD"])
    halted = evaluate(signal, drawdown=0.2)
    assert halted.allowed is False
    gapped = evaluate(signal, gap_pct=0.1)
    assert any("gap" in reason for reason in gapped.reasons)


def test_short_series_rejected():
    with pytest.raises(ValueError):
        signal_for(group_by_symbol(load_candles(FIXTURE))["BTC-USD"][:3])
    with pytest.raises(ValueError):
        Candle("X", AssetClass.MAJOR, "t", 10, 9, 8, 10, 1)
