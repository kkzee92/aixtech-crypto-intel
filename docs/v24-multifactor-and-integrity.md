# Version 0.24 multi-factor strategy overlays and strategy-integrity plane

`crypto-intel v24` is a twentieth pass. Multi-factor confirmation (volume, momentum, relative strength, adaptive ATR) and a strategy-integrity digest check can only shrink paper size. They do not open a socket, store key material, place an order, or enable live trading.

| Class | v0.24 multi-factor | Effect if failed |
|-------|--------------------|------------------|
| Major | Adaptive EMA + RSI + MACD proxy + volume | Zero on stress/extreme RSI; half otherwise |
| Large-cap alt | Volume + relative strength vs BTC | Zero on lag or missing volume |
| Stablecoin | Peg velocity + persistence | Size stays zero; alert severity raised |
| DeFi | Realized vol + gap + volume | Zero on high vol or gap |
| Meme | Burst quality + anti-chase + volume | Zero on extension or decay |
| L2 | Excess return + benchmark non-stress + fee proxy | Zero on lag or stressed benchmark |
| RWA | Slow trend + gap + staleness | Zero on gap or stale |
| Perpetual | Funding containment + drift + sign stability | Zero on extreme or flip |

`crypto-intel integrity` publishes a parameter digest and refuses directional size on mismatch.  
`crypto-intel v24` applies the overlays.  
The strategy-integrity plane has no execution zone. Trade, withdrawal, seed, and private-key scopes remain refused.

This is a research control, not a certification. All prior version invariants remain in force.
