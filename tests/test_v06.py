import pytest

from crypto_intel.catalog import OVERLAYS, parameter_digest
from crypto_intel.cyber import (
    assert_key_scope,
    assert_no_seed_material,
    incident_playbook,
    key_ceremony,
    research_packet,
)
from crypto_intel.enhance import apply_class_enhancement
from crypto_intel.models import AssetClass, Candle, Side


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


def test_class_enhancements_can_only_shrink_and_stay_paper():
    closes = [100, 112, 100, 114, 99, 116, 98, 118, 97, 120, 96, 122, 95, 124, 94, 126]
    major = _series("BTC-USD", AssetClass.MAJOR, closes)
    damped = apply_class_enhancement(major, proposed_size=0.08, side=Side.LONG)
    assert damped["size_fraction"] <= 0.04
    assert damped["live_enabled"] is False
    assert damped["can_increase_size"] is False

    volumes = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0.5]
    fading = _series("SOL-USD", AssetClass.LARGE_CAP_ALT, [20 + i for i in range(10)], volumes=volumes)
    vetoed = apply_class_enhancement(fading, proposed_size=0.04, side=Side.LONG)
    assert vetoed["size_fraction"] == 0.0

    wide = _series("AAVE-USD", AssetClass.DEFI, [100] * 8, range_pct=0.1)
    halted = apply_class_enhancement(wide, proposed_size=0.02, side=Side.LONG)
    assert halted["size_fraction"] == 0.0

    peg = _series("USDC-USD", AssetClass.STABLECOIN, [1.003, 1.003, 1.003, 1.003, 1.003, 1.003, 1.004, 1.004])
    stable = apply_class_enhancement(peg, proposed_size=0.05, side=Side.LONG)
    assert stable["size_fraction"] == 0.0


def test_l2_rwa_and_perp_enhancements():
    bench = _series("ETH-USD", AssetClass.MAJOR, [100 * (1.02**i) for i in range(10)])
    lagging = _series("ARB-USD", AssetClass.L2, [100 - i for i in range(10)])
    l2 = apply_class_enhancement(lagging, proposed_size=0.03, side=Side.LONG, benchmark=bench)
    assert l2["size_fraction"] == 0.0

    fast = _series("ONDO-USD", AssetClass.RWA, [100 * (1.02**i) for i in range(12)])
    rwa = apply_class_enhancement(fast, proposed_size=0.02, side=Side.LONG)
    assert rwa["size_fraction"] == 0.0

    crowded = _series("BTC-PERP", AssetClass.PERPETUAL, [100 + i for i in range(10)], funding=0.004)
    perp = apply_class_enhancement(crowded, proposed_size=0.02, side=Side.LONG)
    assert perp["size_fraction"] == 0.0
    assert float(OVERLAYS["class_enhance"]["perp_funding_halt"]) == 0.003


def test_cyber_scope_ceremony_and_packet():
    assert assert_key_scope("market_read") == "market_read"
    with pytest.raises(PermissionError):
        assert_key_scope("trade")
    with pytest.raises(PermissionError):
        assert_key_scope("withdraw_all")
    with pytest.raises(PermissionError):
        assert_no_seed_material("operator pasted a seed phrase into the ticket")
    ceremony = key_ceremony()
    playbook = incident_playbook()
    assert ceremony["seed_in_repo"] is False
    assert ceremony["automated_keygen"] is False
    assert playbook["automated_remediation"] is False
    assert playbook["live_enabled"] is False
    packet = research_packet(parameter_digest(), "SYNTHETIC")
    assert packet["packet_digest"] == research_packet(parameter_digest(), "SYNTHETIC")["packet_digest"]
    with pytest.raises(ValueError):
        research_packet(parameter_digest(), "customer_export")
