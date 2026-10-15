# Version 0.7 enhancements: further adaptive multi-factor strategies and cyber resilience

Research update for the paper-only crypto trading information system. Builds on v0.6 multi-factor (EMA, MACD, Bollinger-style, vol scaling) with additional trend strength confirmation and refined anomaly handling. Not financial advice; scores describe synthetic fixtures only.

## Strategy enhancements (per asset class)

- **Major**: Added simple trend strength proxy (directional movement ratio) requiring positive strength for trend entries; refined BB confirmation to prefer expansion.
- **Large-cap alt**: Breakout now requires trend strength > threshold in addition to volume/MACD/momentum; adaptive based on vol.
- **Stablecoin**: Added multi-bar sustained deviation check (already partially present; reinforced).
- **DeFi**: Trend strength filter added to calm regime entries.
- **Meme**: Burst requires consistent directional closes (3 rising) plus strength proxy.
- **L2**: Relative strength now also checks own trend strength vs benchmark.
- **RWA**: Slow trend requires positive trend strength over longer window.
- **Perpetual**: Carry entry requires contained trend strength (not extreme directional).

All sizes remain volatility-scaled. Regime overlay and stress stand-aside unchanged. Paper-only preserved.

## Security and data architecture enhancements

- Expanded SECRET_PATTERNS with additional mnemonic and key formats.
- Anomaly scoring note added for consecutive jumps (research helper).
- Reinforced zero-trust: independent re-evaluation per bar; no state carry-over of signals.
- Series integrity remains SHA-256; documented optional rolling checksum for future.
- Continued PDPA tripwire, gitleaks, paper-only mode, no live keys, RBAC with no trader role.

These remain research heuristics. A production system would require separate human-approved broker integration, formal threat modeling, compliance review, and real market data (never in this repo).

See updated `src/crypto_intel/strategies.py` and `docs/security-architecture.md`. This version is 0.7.0.
