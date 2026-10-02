from pathlib import Path

import pytest

from crypto_intel.classification import DataClass, assert_research_label, classify_label, retention_days
from crypto_intel.cross_asset import apply_cross_overlay, basket_report
from crypto_intel.intel import inform
from crypto_intel.market import group_by_symbol, load_candles
from crypto_intel.models import AssetClass, Candle
from crypto_intel.relative import major_relative
from crypto_intel.threats import threat_report
from crypto_intel.walkforward import split_walkforward

FIXTURE = Path(__file__).parents[1] / "fixtures" / "candles_synthetic.json"


def _series(symbol: str, asset_class: AssetClass, closes: list[float], range_pct: float = 0.02) -> list[Candle]:
    rows = []
    for index, close in enumerate(closes):
        rows.append(
            Candle(
                symbol,
                asset_class,
                f"2026-02-{index + 1:02d}T00:00:00Z",
                close,
                close * (1 + range_pct),
                close * (1 - range_pct),
                close,
                5000,
            )
        )
    return rows


def test_relative_sleeve_names_the_leader_and_stands_aside_in_stress():
    btc = _series("BTC-USD", AssetClass.MAJOR, [100 + i for i in range(10)])
    eth = _series("ETH-USD", AssetClass.MAJOR, [50 * (1.02**i) for i in range(10)])
    report = major_relative(btc, eth)
    assert report["sleeve"] == "eth_btc_relative"
    assert report["size_fraction"] <= 0.02
    assert report["live_enabled"] is False
    stressed = _series("BTC-USD", AssetClass.MAJOR, [100, 80, 120, 70, 130, 60, 140, 50, 150, 40], range_pct=0.05)
    stood_aside = major_relative(stressed, eth)
    assert stood_aside["leader"] == "flat"
    assert stood_aside["size_fraction"] == 0.0


def test_cross_asset_spillover_and_stablecoin_contagion():
    stressed = _series("BTC-USD", AssetClass.MAJOR, [100, 80, 120, 70, 130, 60, 140, 50, 150, 40], range_pct=0.05)
    alt = _series("SOL-USD", AssetClass.LARGE_CAP_ALT, [20 + i * 0.4 for i in range(10)])
    usdc = _series("USDC-USD", AssetClass.STABLECOIN, [1.0] * 9 + [0.99])
    usdt = _series("USDT-USD", AssetClass.STABLECOIN, [1.0] * 9 + [0.997])
    grouped = {"BTC-USD": stressed, "SOL-USD": alt, "USDC-USD": usdc, "USDT-USD": usdt}
    report = basket_report(grouped)
    assert report["beta_spillover"] is True
    assert report["stablecoin_contagion"] is True
    row = inform(alt)
    vetoed = apply_cross_overlay(row, report)
    assert vetoed["size_fraction"] == 0.0
    assert vetoed["live_enabled"] is False


def test_data_classification_refuses_personal_and_secret_labels():
    assert classify_label("SYNTHETIC") is DataClass.SYNTHETIC
    assert assert_research_label("PUBLIC_READ") is DataClass.PUBLIC_MARKET
    assert retention_days(DataClass.SECRET) == 0
    assert retention_days(DataClass.SYNTHETIC) is None
    with pytest.raises(PermissionError):
        assert_research_label("customer_nric_export")
    with pytest.raises(PermissionError):
        assert_research_label("exchange_api_key_dump")
    with pytest.raises(ValueError):
        classify_label("unlabelled")


def test_threat_map_covers_every_stride_row():
    report = threat_report()
    assert report["coverage"] is True
    assert report["live_enabled"] is False
    strides = {row["stride"] for row in report["threats"]}
    expected = {"spoofing", "tampering", "repudiation", "information_disclosure", "denial_of_service", "elevation"}
    assert expected <= strides


def test_walkforward_split_is_labelled_research():
    grouped = group_by_symbol(load_candles(FIXTURE))
    report = split_walkforward(grouped["BTC-USD"])
    assert report["train_bars"] < len(grouped["BTC-USD"])
    assert report["live_enabled"] is False
    assert "Not a forecast" in report["note"]
