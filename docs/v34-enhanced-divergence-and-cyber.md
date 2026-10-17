# v0.10 Enhancement Log: Divergence Filters, VWAP Proxy, and Cyber Hardening

Version 0.10 builds on v0.9 with additional research factors and security controls.
All changes remain paper-only and research-oriented.

## Strategy enhancements

- Added simple RSI divergence proxy (price higher high + RSI lower high, or vice versa) for mean-reversion confirmation on Major and DeFi.
- Introduced lightweight VWAP proxy (volume-weighted average over recent bars) as additional confirmation for trend entries on Major and Large-cap alt.
- Extended correlation proxy window option and applied slightly stricter threshold for L2.
- Adaptive volume and strength thresholds refined with ATR scaling in a few classes.
- Volatility scaling, regime overlays, stochastic, MACD, BB, and median volume unchanged in principle.

## Security and data architecture

- Expanded SECRET_PATTERNS for 64-character hex private-key styles and Telegram bot token styles.
- Enhanced anomaly_score with volume Z-score component for better thin-print detection.
- Added series_consistency_check helper (simple cross-print price continuity research flag).
- Reinforced zero-trust: callers must re-validate all inputs; no persistent secrets; key separation notes updated.
- Continued hash-chained audit, expanded redaction, sanitization, and paper-only guards.

## Still out of scope

- Live order routing or exchange connectors.
- Storage of any secrets.
- Claims of predictive performance.

See updated docs/asset-class-strategies.md and docs/security-architecture.md for full details.
