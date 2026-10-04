from pathlib import Path

from crypto_intel.cli import main
from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v10 import CLASS_DATA_POLICY, PASS_NOTES, apply_v10, cyber_architecture_report, evidence_digest

FIXTURE = Path(__file__).parents[1] / "fixtures" / "candles_synthetic.json"


def _series(symbol: str, asset_class: AssetClass, closes: list[float], *, volume: float = 1000.0, range_pct: float = 0.01) -> list[Candle]:
    rows = []
    for index, close in enumerate(closes):
        half = close * range_pct
        rows.append(
            Candle(
                symbol,
                asset_class,
                f"2026-01-{index+1:02d}T00:00:00Z",
                close,
                close + half,
                close - half,
                close,
                volume,
            )
        )
    return rows


def test_every_class_has_a_pass_and_data_policy():
    assert set(PASS_NOTES) == {item.value for item in AssetClass}
    assert set(CLASS_DATA_POLICY) == set(PASS_NOTES)


def test_pass_cannot_increase_size_and_stable_stays_zero():
    quiet = apply_v10(_series("BTC-USD", AssetClass.MAJOR, [100] * 8), proposed_size=0.08, side=Side.LONG)
    assert quiet["size_fraction"] == 0.08
    assert quiet["can_increase_size"] is False
    assert quiet["order_path"] is False
    raised = apply_v10(_series("BTC-USD", AssetClass.MAJOR, [100] * 8), proposed_size=0.01, side=Side.LONG)
    assert raised["size_fraction"] <= 0.01
    stable = apply_v10(_series("USDC-USD", AssetClass.STABLECOIN, [1.002] * 8), proposed_size=0.02, side=Side.LONG)
    assert stable["size_fraction"] == 0.0
    assert "zero" in str(stable["note"])


def test_class_guards_shrink_on_their_trigger():
    thin = _series("BTC-USD", AssetClass.MAJOR, [100] * 8)
    thin[-1] = Candle(thin[-1].symbol, thin[-1].asset_class, thin[-1].timestamp, 100, 101, 99, 100, 100)
    major = apply_v10(thin, proposed_size=0.08, side=Side.LONG)
    assert major["size_fraction"] == 0.04

    alt = _series("SOL-USD", AssetClass.LARGE_CAP_ALT, [100] * 8, range_pct=0.001)
    last = alt[-1]
    alt[-1] = Candle(last.symbol, last.asset_class, last.timestamp, last.open, last.high, last.low, last.close, 5000)
    assert apply_v10(alt, proposed_size=0.04, side=Side.LONG)["size_fraction"] == 0.0

    defi = _series("AAVE-USD", AssetClass.DEFI, [100] * 8)
    prev = defi[-1]
    defi[-1] = Candle(prev.symbol, prev.asset_class, prev.timestamp, prev.open, prev.high, prev.low, prev.close, 100)
    assert apply_v10(defi, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01

    meme = _series("PEPE-USD", AssetClass.MEME, [1] * 8, range_pct=0.02)
    bar = meme[-1]
    meme[-1] = Candle(bar.symbol, bar.asset_class, bar.timestamp, 1.0, 1.05, 0.95, 0.97, bar.volume)
    assert apply_v10(meme, proposed_size=0.005, side=Side.LONG)["size_fraction"] == 0.0

    own = _series("ARB-USD", AssetClass.L2, [100] * 8, range_pct=0.04)
    bench = _series("ETH-USD", AssetClass.MAJOR, [100] * 8)
    assert apply_v10(own, proposed_size=0.03, side=Side.LONG, benchmark=bench)["size_fraction"] == 0.015
    assert apply_v10(own, proposed_size=0.03, side=Side.LONG)["size_fraction"] == 0.0

    rwa = _series("ONDO-USD", AssetClass.RWA, [100] * 8)
    previous = rwa[-2]
    rwa[-1] = Candle(previous.symbol, previous.asset_class, rwa[-1].timestamp, 104, 105, 103, 104, previous.volume)
    assert apply_v10(rwa, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.0

    perp = _series("BTC-PERP", AssetClass.PERPETUAL, [100, 100, 100, 101, 104, 108, 112, 118])
    assert apply_v10(perp, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.0


def test_cyber_architecture_has_no_execution_zone():
    report = cyber_architecture_report()
    assert report["live_enabled"] is False
    assert report["execution_zone"] is False
    assert report["order_path"] is False
    assert report["evidence_digest"] == evidence_digest()
    assert len(report["class_data_policy"]) == 8
    assert "default-deny" in str(report["egress"])


def test_v10_commands(capsys):
    assert main(["cyberarch"]) == 0
    assert main(["v10", str(FIXTURE)]) == 0
    out = capsys.readouterr().out
    assert "evidence_digest" in out
    assert "order_path" in out
    assert "false" in out.lower() or "False" in out
