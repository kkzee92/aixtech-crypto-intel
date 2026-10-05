"""v0.10 liquidity guards and cyber plane."""

from crypto_intel.models import AssetClass, Candle, Side
from crypto_intel.v10 import apply_v10, cyber_plane_report, information_pack


def _bars(
    asset_class: AssetClass, *, volume: float = 100.0, funding: float = 0.0, close: float = 100.0
) -> list[Candle]:
    rows = []
    for index in range(12):
        price = close + index * 0.1
        rows.append(
            Candle(
                symbol="TEST",
                asset_class=asset_class,
                timestamp=f"2026-01-01T{index:02d}:00:00Z",
                open=price,
                high=price + 1,
                low=price - 1,
                close=price,
                volume=volume,
                funding_rate=funding,
            )
        )
    return rows


def test_major_thin_book_haircut_cannot_raise_size() -> None:
    bars = _bars(AssetClass.MAJOR, volume=100.0)
    thin = bars[:-1] + [
        Candle(
            symbol="TEST",
            asset_class=AssetClass.MAJOR,
            timestamp="2026-01-01T12:00:00Z",
            open=101,
            high=102,
            low=100,
            close=101,
            volume=10,
        )
    ]
    row = apply_v10(thin, proposed_size=0.08, side=Side.LONG)
    assert row["size_fraction"] == 0.04
    assert row["can_increase_size"] is False
    assert row["order_path"] is False
    assert row["live_enabled"] is False


def test_stablecoin_size_stays_zero() -> None:
    bars = _bars(AssetClass.STABLECOIN, close=1.0)
    row = apply_v10(bars, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert row["side"] == "flat"


def test_meme_volume_collapse_veto() -> None:
    bars = _bars(AssetClass.MEME, volume=100.0)
    collapsed = bars[:-1] + [
        Candle(
            symbol="TEST",
            asset_class=AssetClass.MEME,
            timestamp="2026-01-01T12:00:00Z",
            open=101,
            high=102,
            low=100,
            close=101,
            volume=10,
        )
    ]
    row = apply_v10(collapsed, proposed_size=0.005, side=Side.LONG)
    assert row["size_fraction"] == 0.0
    assert "volume-collapse" in str(row["note"])


def test_perp_funding_flip_veto() -> None:
    bars = _bars(AssetClass.PERPETUAL, funding=0.0001)
    flipped = bars[:-2] + [
        Candle("TEST", AssetClass.PERPETUAL, "2026-01-01T10:00:00Z", 100, 101, 99, 100, 100, -0.0002),
        Candle("TEST", AssetClass.PERPETUAL, "2026-01-01T11:00:00Z", 100, 101, 99, 100, 100, 0.0002),
    ]
    row = apply_v10(flipped, proposed_size=0.02, side=Side.LONG)
    assert row["size_fraction"] == 0.0


def test_information_pack_haircut_and_cyber_plane() -> None:
    rows = [{"symbol": f"S{i}", "asset_class": "major", "size_fraction": 0.02} for i in range(4)]
    pack = information_pack(rows)
    assert pack["breadth_haircut"] == 0.75
    assert pack["order_instruction"] is False
    assert all(item["size_fraction"] <= item["prior_size"] for item in pack["rows"])
    plane = cyber_plane_report()
    assert plane["execution_zone"] is False
    assert plane["order_path"] is False
    assert all(item["can_trade"] is False for item in plane["key_separation"])
