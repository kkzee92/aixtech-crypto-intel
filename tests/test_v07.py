import pytest

from crypto_intel.catalog import OVERLAYS
from crypto_intel.liquidity import apply_liquidity_gate
from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.residency import (
    assert_research_label,
    assert_store_region,
    residency_report,
)


def _series(
    symbol: str,
    asset_class: AssetClass,
    closes: list[float],
    *,
    volumes: list[float] | None = None,
    funding: float = 0.0,
    range_pct: float = 0.01,
) -> list[Candle]:
    rows = []
    for index, close in enumerate(closes):
        volume = 5000.0 if volumes is None else volumes[index]
        rows.append(
            Candle(
                symbol,
                asset_class,
                f"2026-03-{index + 1:02d}T00:00:00Z",
                close,
                close * (1 + range_pct),
                close * (1 - range_pct),
                close,
                volume,
                funding,
            )
        )
    return rows


def test_liquidity_gates_can_only_shrink():
    thin = _series(
        "BTC-USD",
        AssetClass.MAJOR,
        [100 + i for i in range(8)],
        volumes=[100, 100, 100, 100, 100, 100, 100, 10],
    )
    major = apply_liquidity_gate(thin, proposed_size=0.08, side=Side.LONG)
    assert major["size_fraction"] == 0.04
    assert major["can_increase_size"] is False
    assert major["live_enabled"] is False

    wide = _series("SOL-USD", AssetClass.LARGE_CAP_ALT, [20 + i for i in range(8)], range_pct=0.05)
    alt = apply_liquidity_gate(wide, proposed_size=0.04, side=Side.LONG)
    assert alt["size_fraction"] == 0.0
    assert float(OVERLAYS["liquidity"]["alt_range_veto"]) == 0.03

    meme = _series("DOGE-USD", AssetClass.MEME, [1] * 8, volumes=[100] * 8)
    assert apply_liquidity_gate(meme, proposed_size=0.005, side=Side.LONG)["size_fraction"] == 0.0

    stable = _series("USDC-USD", AssetClass.STABLECOIN, [1] * 8)
    assert apply_liquidity_gate(stable, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.0


def test_defi_l2_rwa_and_perp_liquidity():
    wide_defi = _series("AAVE-USD", AssetClass.DEFI, [100] * 8, range_pct=0.08)
    assert apply_liquidity_gate(wide_defi, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.0

    thin_l2 = _series(
        "ARB-USD",
        AssetClass.L2,
        [10] * 8,
        volumes=[200, 200, 200, 200, 200, 200, 200, 40],
    )
    l2 = apply_liquidity_gate(thin_l2, proposed_size=0.03, side=Side.LONG)
    assert l2["size_fraction"] == 0.015

    thin_rwa = _series(
        "ONDO-USD",
        AssetClass.RWA,
        [10] * 8,
        volumes=[80, 80, 80, 80, 80, 80, 80, 10],
    )
    assert apply_liquidity_gate(thin_rwa, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01

    crowded = _series(
        "BTC-PERP",
        AssetClass.PERPETUAL,
        [100] * 8,
        volumes=[100, 100, 100, 100, 100, 100, 100, 400],
        funding=0.002,
    )
    perp = apply_liquidity_gate(crowded, proposed_size=0.02, side=Side.SHORT)
    assert perp["size_fraction"] == 0.01
    assert "crowded tape" in str(perp["note"])


def test_residency_refuses_personal_and_unknown_regions():
    assert assert_research_label("SYNTHETIC") == "SYNTHETIC"
    assert assert_store_region("ap-southeast-1") == "ap-southeast-1"
    with pytest.raises(PermissionError):
        assert_research_label("customer")
    with pytest.raises(PermissionError):
        assert_research_label("secret")
    with pytest.raises(PermissionError):
        assert_store_region("unknown-region")
    report = residency_report()
    assert report["live_enabled"] is False
    assert report["encryption"]["key_in_repo"] is False
    assert report["vendor"]["withdrawal_scope"] is False
    assert report["retention"]["personal"]["retention_days"] == 0
