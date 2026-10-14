# Version 0.5 enhancements: asset-class strategies and cyber/data security

This document records further research enhancements to the paper-only automated cryptocurrency trading information system.

## Strategy enhancements (per asset class)

- **Major**: MACD histogram proxy confirmation added to EMA + RSI + momentum. Tighter range-reversion RSI (<28). Confidence slightly raised on confirmed trend.
- **Large-cap alt**: Volume threshold raised to 1.4x average. Multi-bar close consistency (at least 2 of last 3 higher closes) required.
- **Stablecoin**: Watch band tightened to 40 bps; depeg alert at 80 bps for earlier detection.
- **DeFi**: Realised-vol stand-aside lowered to 5.5%. Volume support preferred above 0.9x recent average.
- **Meme**: Burst threshold reduced to 12% over 3 bars. Liquidity floor raised to 1500. Extension filter tightened to 30%.
- **L2**: Excess return requirement raised to 3.5%. Own ATR containment tightened to <3.5%.
- **RWA**: Gap halt tightened to 7%. Momentum confirmation retained.
- **Perpetual**: Funding entry at or below -6 bps; crowded alert at 12 bps. Drift containment to 3.5%; ATR to 4.5%.

All directional sizes remain volatility-scaled inversely to recent ATR. Adaptive filters reduce false positives on synthetic fixtures. Zero-trust: every signal re-evaluated by risk gate.

## Cyber and data security architecture enhancements

- Strengthened data classification and redaction coverage for private-key proxies, seeds, and wallet-like identifiers.
- Expanded control catalog notes for series integrity digests and zero-trust re-evaluation.
- Incident playbook continues to emphasize kill-switch containment with dual-control clear; no automated live path.
- Continued paper-only enforcement, egress allowlist, PDPA tripwire, hash-chained audit, and source attestation.
- Operating rule: adaptive multi-factor filters and vol scaling are research overlays only; they cannot increase size or enable live execution.

These remain research heuristics. Scores describe the synthetic fixture, not future returns. Not financial, legal, or compliance advice. No live order routing or trade keys.

See updated `src/crypto_intel/strategies.py`, `docs/asset-class-strategies.md`, and `docs/security-architecture.md`.
