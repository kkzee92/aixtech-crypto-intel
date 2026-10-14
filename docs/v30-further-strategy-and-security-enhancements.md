# Version 0.5 enhancements: strategies and security

This document records further research enhancements to the paper-only crypto trading information system.

## Strategy enhancements (per asset class)

- **Major**: Added simplified MACD histogram confirmation (positive hist required alongside EMA/RSI). Tighter range reversion RSI (<28).
- **Large-cap alt**: Increased volume threshold to 1.4x, added multi-bar close consistency (at least 2 of last 3 higher closes).
- **Stablecoin**: Tightened watch band to 40 bps and depeg to 80 bps for earlier alerts.
- **DeFi**: Lowered realised-vol stand-aside to 5.5%, preferred volume >0.9x average.
- **Meme**: Reduced burst threshold to 12% over 3 bars, raised liquidity floor to 1500, tightened extension to 30%.
- **L2**: Raised excess return requirement to 3.5%, tightened own ATR filter to <3.5%.
- **RWA**: Tightened gap halt to 7%, retained momentum confirmation.
- **Perpetual**: Adjusted funding thresholds (-6 bps entry, 12 bps crowded), tighter drift (3.5%) and ATR (4.5%) containment.

All directional sizes remain volatility-scaled inversely to recent ATR. These filters reduce false positives on synthetic fixtures while remaining research heuristics.

## Security architecture enhancements

- Continued expansion of data classification for series integrity and redaction of private-key/seed proxies.
- Strengthened zero-trust re-evaluation of every signal by the risk gate.
- Additional operating rule: adaptive multi-factor filters and tighter class-specific thresholds reduce noise.
- Emphasis remains on paper-only mode, no live keys, hash-chained audit, PDPA tripwire, source attestation, and series integrity digests.

These remain research heuristics. Scores describe the synthetic fixture, not future returns. Not financial, legal, or compliance advice.

See updated `src/crypto_intel/strategies.py` and `docs/security-architecture.md` for implementation details.
