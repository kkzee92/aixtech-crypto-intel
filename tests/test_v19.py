"""v0.19 microstructure guards, information tape, and secrets lifecycle."""

import pytest

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v19 import acknowledge_rotation, apply_v19, information_tape, scope_decision, secrets_lifecycle


def _bars(
    asset_class: AssetClass,
    *,
    volume: float = 100.0,
    funding: float = 0.0,
    close: float = 100.0,
    step: float = 0.1,
) -> list[Candle]:
    rows = []
    for index in range(12):
        price = close + index * step
        rows.append(
            Candle(
                symbol="TEST",
                asset_class=asset_class,
                timestamp=f"2026-01-01T{index:02d}:00:00Z",
                open=price,
                high=price + 1,
                low=price - 1,
                close=price,
                volume=volume + index,
                funding_rate=funding,
            )
        )
    return rows


def test_major_gap_and_fail_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR, close=100.0, step=0.0)
    failed = bars[:-1] + [
        Candle("TEST", AssetClass.MAJOR, "2026-01-01T11:00:00Z", 102, 103, 100, 101, 100),
    ]
    row = apply_v19(failed, proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.04
    assert row["can_increase_size"] is False
    quiet = apply_v19(bars, proposed_size=0.08, side=Side.LONG)
    assert quiet["size_fraction"] == 0.08
    assert "not triggered" in str(quiet["note"])


def test_alt_upper_wick_haircut() -> None:
    bars = _bars(AssetClass.LARGE_CAP_ALT)
    wicked = bars[:-1] + [
        Candle("TEST", AssetClass.LARGE_CAP_ALT, "2026-01-01T11:00:00Z", 100, 110, 99, 101, 100),
    ]
    row = apply_v19(wicked, proposed_size=0.04, side=Side.LONG)
    assert row["size_fraction"] == 0.02
    assert apply_v19(bars, proposed_size=0.04, side=Side.LONG)["size_fraction"] == 0.04


def test_stablecoin_velocity_stays_flat() -> None:
    bars = _bars(AssetClass.STABLECOIN, close=1.0, step=0.0)
    drifting = bars[:-4] + [
        Candle("TEST", AssetClass.STABLECOIN, f"2026-01-01T{index:02d}:00:00Z", 1.002, 1.003, 1.001, 1.002, 10)
        for index in range(8, 12)
    ]
    row = apply_v19(drifting, proposed_size=0.02, side=Side.ALERT)
    assert row["size_fraction"] == 0.0
    assert row["side"] == "flat"
    assert "velocity" in str(row["note"])
    quiet = apply_v19(bars, proposed_size=0.02, side=Side.FLAT)
    assert "size stays zero" in str(quiet["note"])


def test_defi_divergence_and_meme_veto() -> None:
    defi = _bars(AssetClass.DEFI, close=100.0, step=1.0)
    defi = defi[:-3] + [
        Candle("TEST", AssetClass.DEFI, "2026-01-01T09:00:00Z", 108, 109, 107, 108, 300),
        Candle("TEST", AssetClass.DEFI, "2026-01-01T10:00:00Z", 109, 110, 108, 109, 200),
        Candle("TEST", AssetClass.DEFI, "2026-01-01T11:00:00Z", 110, 111, 109, 111, 100),
    ]
    assert apply_v19(defi, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01
    assert "not triggered" in str(apply_v19(_bars(AssetClass.DEFI), proposed_size=0.02, side=Side.LONG)["note"])
    meme = _bars(AssetClass.MEME)[:-1] + [
        Candle("TEST", AssetClass.MEME, "2026-01-01T11:00:00Z", 100, 112, 99, 101, 500),
    ]
    veto = apply_v19(meme, proposed_size=0.005, side=Side.LONG)
    assert veto["size_fraction"] == 0.0
    assert "veto" in str(veto["note"])


def test_l2_dispersion_rwa_gap_and_perp_disagreement() -> None:
    l2 = _bars(AssetClass.L2)[:-1] + [
        Candle("TEST", AssetClass.L2, "2026-01-01T11:00:00Z", 100, 106, 94, 101, 100),
    ]
    assert apply_v19(l2, proposed_size=0.03, side=Side.LONG)["size_fraction"] == 0.015
    assert "not triggered" in str(apply_v19(_bars(AssetClass.L2), proposed_size=0.03, side=Side.LONG)["note"])
    rwa = _bars(AssetClass.RWA, close=100.0, step=0.0)[:-1] + [
        Candle("TEST", AssetClass.RWA, "2026-01-01T11:00:00Z", 103, 104, 102, 103, 100),
    ]
    assert apply_v19(rwa, proposed_size=0.02, side=Side.LONG)["size_fraction"] == 0.01
    perp = _bars(AssetClass.PERPETUAL, close=100.0, step=1.0, funding=-0.0008)
    row = apply_v19(perp, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.01
    quiet = apply_v19(_bars(AssetClass.PERPETUAL, funding=0.0), proposed_size=0.02, side=Side.SHORT)
    assert quiet["size_fraction"] == 0.02


def test_tape_digest_is_not_an_order() -> None:
    rows = [apply_v19(_bars(AssetClass.MAJOR), proposed_size=0.04, side=Side.LONG)]
    packet = information_tape(rows)
    again = information_tape(rows)
    assert packet["paper_only"] is True
    assert packet["order_path"] is False
    assert packet["can_enable_live"] is False
    assert packet["tape_digest"] == again["tape_digest"]
    assert packet["class_counts"]["major"] == 1


def test_secrets_lifecycle_refuses_trade_scopes() -> None:
    plane = secrets_lifecycle()
    assert plane["execution_zone"] is False
    assert plane["material_stored"] is False
    assert scope_decision("market_read_public", 91)["rotate"] is True
    assert scope_decision("audit_sign_research", 10)["rotate"] is False
    assert scope_decision("break_glass_review", 30)["rotate"] is True
    refused = scope_decision("exchange_trade_key", 1)
    assert refused["accepted"] is False
    assert scope_decision("unknown_key", 1)["accepted"] is False
    assert acknowledge_rotation({"researcher"})["acknowledged"] is False
    signed = acknowledge_rotation({"researcher", "auditor"})
    assert signed["acknowledged"] is True
    assert signed["can_enable_live"] is False
    assert all(duty["can_trade"] is False for duty in plane["duties"])


def test_short_series_rejected() -> None:
    with pytest.raises(ValueError):
        apply_v19(_bars(AssetClass.MAJOR)[:3], proposed_size=0.01, side=Side.LONG)
