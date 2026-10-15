# Version 0.6 enhancements: multi-factor adaptive strategies and cyber resilience

Research update for the paper-only crypto trading information system. Continues
the series of iterative improvements to asset-class heuristics and data/cyber
security architecture. Not financial advice; scores describe synthetic fixtures
only.

## Strategy enhancements (per asset class)

- **Major**: Added Bollinger-band-style envelope confirmation (price near or above mid-band with positive slope) alongside multi-EMA + MACD. Adaptive RSI band further refined by recent ATR.
- **Large-cap alt**: Volume confirmation now also requires relative volume vs 20-bar baseline where available; multi-bar momentum threshold raised slightly in high-vol regimes.
- **Stablecoin**: Added secondary watch for sustained deviation (2 of last 3 bars outside band) to reduce single-print noise.
- **DeFi**: Realised-vol stand-aside now also considers ATR percentile; preferred positive slope on the 8-bar EMA.
- **Meme**: Burst filter now requires both price and volume acceleration; extension limit made adaptive to recent realised vol.
- **L2**: Relative strength threshold slightly adaptive; added optional correlation filter proxy (simple co-movement check) when benchmark series is long enough.
- **RWA**: Gap halt remains adaptive; added requirement that the slow trend has positive slope over the horizon window.
- **Perpetual**: Funding stability window extended to last 3 prints; drift containment now uses ATR-scaled absolute limit.

All sizes remain volatility-scaled. Regime overlay and stress stand-aside unchanged.

## Security and data architecture enhancements

- Strengthened series integrity: optional multi-hash (SHA-256 + simple rolling checksum) for fixture attestation.
- Expanded redaction patterns for additional token formats and long numeric secrets.
- Zero-trust re-evaluation note reinforced: every paper signal is independently gated; no carry-over of prior confidence.
- Cyber resilience: documented kill-switch + audit freeze procedure more explicitly; added note on feed-jump isolation.
- Continued PDPA tripwire, gitleaks, paper-only mode, no live keys, RBAC with no trader role.

These remain research heuristics. A production system would require separate human-approved broker integration, formal threat modeling, and compliance review.

See `src/crypto_intel/strategies.py` (minor adaptive additions) and `docs/security-architecture.md` for current implementation. This version is 0.6.0.
