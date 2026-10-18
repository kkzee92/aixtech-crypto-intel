# v0.14 Enhancement Log: CCI Confirmation, Volume MAD, and Strengthened Integrity

Version 0.14 adds Commodity Channel Index (CCI) as an additional multi-factor confirmation for Major and Large-cap alt strategies, a mean absolute deviation (MAD) proxy for more robust volume profiling, refined anomaly scoring incorporating CCI extremes, and further cyber/data security hardening.

All changes remain strictly paper-only, research-oriented, with no live execution paths.

## Strategy enhancements per asset class

- **Major**: CCI contained (-100 to 100) required alongside existing multi-EMA, MACD, BB, trend strength, stochastic, VWAP, and adaptive RSI for trend entries. Confidence slightly raised on full alignment.
- **Large-cap alt**: CCI contained (-150 to 150) added to breakout confirmation with volume, momentum, MACD, strength, stochastic, and VWAP.
- Volume profiles now support optional MAD-based outlier detection in addition to median/IQR.
- Adaptive confidence continues to scale with confirming factors; volatility scaling and class caps preserved.
- Other classes (Stablecoin, DeFi, Meme, L2, RWA, Perpetual) retain prior filters with notes for future CCI extension where relevant.

## Cyber and data security architecture

- Additional SECRET_PATTERNS covering more private key variants (extended hex, base58, WIF, and common seed phrase proxies).
- Series integrity digest enhanced with optional CCI-based anomaly flag for extreme readings that may indicate feed issues.
- Anomaly scoring refined to include CCI extremes and volume MAD outliers.
- Reinforced zero-trust: every scan re-validates source attestation, series digest, audit chain, and now CCI consistency where applicable.
- Expanded notes on production research deployment: encryption at rest (AES-256), access logging, data residency (prefer local/on-prem), and key separation (research vs any future paper-sim only).
- Continued: hash-chained audit logs, expanded redaction, paper-only PermissionError guards, PDPA tripwire, gitleaks in CI.

## Still out of scope

- Live order routing, exchange API connectors, or withdrawal scopes.
- Storage of secrets, private keys, or personal data.
- Any claim of predictive edge, certified security, or investment advice.

See updated docs/asset-class-strategies.md and docs/security-architecture.md.
