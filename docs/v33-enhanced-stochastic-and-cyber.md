# v0.9 Enhancement Log: Stochastic Confirmation and Cyber Hardening

Version 0.9 builds on v0.8 with additional research factors and security controls.
All changes remain paper-only and research-oriented.

## Strategy enhancements

- Added stochastic oscillator %K proxy across all directional classes for overbought rejection and washed-out mean-reversion confirmation.
- Strengthened multi-window EMA slope checks.
- Introduced simple Pearson-like correlation proxy for L2 relative-strength signals versus benchmark.
- Adaptive stochastic thresholds alongside existing RSI, volume (median), MACD, BB, and trend strength.
- Volatility scaling and regime overlays unchanged in principle.

## Security and data architecture

- Expanded SECRET_PATTERNS for Discord token styles and Google API key styles.
- Enhanced anomaly_score with Z-score component on recent returns for better jump detection.
- Added timestamp_freshness helper for research feed staleness checks.
- Reinforced notes on key separation: any future market-data credentials must be strictly read-only and distinct from trade/withdrawal credentials.
- Continued hash-chained audit, redaction, sanitization, and zero-trust design.

## Still out of scope

- Live order routing or exchange connectors.
- Storage of any secrets.
- Claims of predictive performance.

See updated docs/asset-class-strategies.md and docs/security-architecture.md for full details.
