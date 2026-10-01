"""Generate labelled synthetic candles. No market data and no personal data."""

from __future__ import annotations

import json
from pathlib import Path

SERIES = (
    ("BTC-USD", "major", 100.0, 0.004, 0.0),
    ("ETH-USD", "major", 50.0, 0.006, 0.0),
    ("SOL-USD", "large_cap_alt", 20.0, 0.01, 0.0),
    ("USDC-USD", "stablecoin", 1.0, 0.0002, 0.0),
    ("AAVE-USD", "defi", 30.0, 0.012, 0.0),
    ("MEME-USD", "meme", 1.0, 0.03, 0.0),
    ("ARB-USD", "l2", 8.0, 0.014, 0.0),
    ("ONDO-USD", "rwa", 12.0, 0.007, 0.0),
    ("BTC-PERP", "perpetual", 100.0, 0.005, -0.0008),
)


def build(bars: int = 16) -> dict:
    candles = []
    for symbol, asset_class, start, drift, funding in SERIES:
        price = start
        for index in range(bars):
            shock = ((index * 17 + len(symbol)) % 7 - 3) / 100.0
            if symbol == "USDC-USD" and index == bars - 1:
                price = 0.99
            elif symbol == "MEME-USD" and index > bars - 5:
                price *= 1.05
            else:
                price *= 1.0 + drift + shock * 0.2
            high = price * 1.01
            low = price * 0.99
            candles.append(
                {
                    "symbol": symbol,
                    "asset_class": asset_class,
                    "timestamp": f"2026-01-{(index % 28) + 1:02d}T00:00:00Z",
                    "open": round(price * 0.999, 6),
                    "high": round(high, 6),
                    "low": round(low, 6),
                    "close": round(price, 6),
                    "volume": 5000 + index * 50 + (10000 if symbol == "MEME-USD" else 0),
                    "funding_rate": funding,
                }
            )
    return {"label": "SYNTHETIC", "note": "Generated fixture. Not market data.", "candles": candles}


def main() -> None:
    target = Path(__file__).resolve().parents[1] / "fixtures" / "candles_synthetic.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
