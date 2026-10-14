# Version 0.4 enhancements: strategies and security

This document records research enhancements to the paper-only crypto trading information system.

## Strategy enhancements (per asset class)

- **Major**: Added simplified MACD histogram confirmation alongside EMA and RSI. Tighter range reversion RSI threshold.
- **Large-cap alt**: Increased volume threshold to 1.4x, added multi-bar close consistency (at least 2 of last 3 higher).
- **Stablecoin**: Tightened watch band to 40 bps and depeg to 80 bps for earlier alerts.
- **DeFi**: Lowered realised-vol stand-aside to 5.5%, preferred volume >0.9x average.
- **Meme**: Reduced burst threshold to 12% over 3 bars, raised liquidity floor to 1500, tightened extension to 30%.
- **L2**: Raised excess return requirement to 3.5%, tightened own ATR filter to <3.5%.
- **RWA**: Tightened gap halt to 7%, retained momentum confirmation.
- **Perpetual**: Adjusted funding thresholds (-6 bps entry, 12 bps crowded), tighter drift (3.5%) and ATR (4.5%) containment.

All directional sizes remain volatility-scaled inversely to recent ATR.

## Security architecture enhancements

- Expanded data classification notes for series integrity and redaction of private-key proxies.
- Strengthened threat model with zero-trust re-evaluation of every signal.
- Additional operating rule: adaptive filters reduce false positives on synthetic fixtures.
- Continued emphasis on paper-only mode, no live keys, hash-chained audit, PDPA tripwire.

These remain research heuristics. Scores describe the synthetic fixture, not future returns. Not financial, legal, or compliance advice.

See updated `src/crypto_intel/strategies.py` and `docs/security-architecture.md` for implementation details.
