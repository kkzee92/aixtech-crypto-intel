# v0.16 Enhancement Log: ADX-Style Trend Strength Proxy and Data Residency Hardening

Version 0.16 introduces an ADX-style directional movement proxy as an additional trend strength confirmation for Major, Large-cap alt, DeFi, and RWA strategies, and strengthens the cyber/data security architecture with explicit data residency, cross-border transfer notes, and refined zero-trust integrity checks.

All changes remain strictly paper-only research. No live execution paths exist. Not financial, legal, or compliance advice.

## Strategy enhancements per asset class

- **Major**: Require ADX-style proxy (directional movement over 14-bar window) above a mild threshold for trend entries, in addition to existing multi-factor stack (EMA, MACD-style, CCI, Williams %R, stochastic, BB, VWAP, adaptive RSI, MTF). Low ADX suppresses trend confidence; range reversion remains available on deep oscillators.
- **Large-cap alt**: ADX-style confirmation required on breakouts to filter weak momentum; combined with volume MAD, CCI, and Williams %R filters.
- **DeFi**: ADX-style strength required in calm regimes; stress or low ADX stands aside more aggressively.
- **RWA**: Slow ADX-style alignment preferred; fast spikes or low strength halt or reduce size.
- **Other classes**: Meme retains burst filters; L2 uses relative ADX-style excess; Stablecoin and Perpetual notes unchanged. Adaptive confidence scales with confirming factors including ADX proxy. Volatility-scaled sizing and class caps unchanged.

## Cyber and data security architecture

- Explicit data residency controls: research fixtures and audit logs prefer Singapore or declared region; cross-border transfer requires attestation.
- Refined zero-trust re-validation: series integrity digest + ADX consistency check + source attestation on every scan.
- Expanded anomaly scoring to include directional inconsistency (ADX proxy vs. price slope divergence).
- Continued: hash-chained audit logs, expanded secret redaction (including additional mnemonic and hex patterns), paper-only PermissionError guards, PDPA tripwire, gitleaks in CI, no trader role, AES-256 at rest recommendation, TLS in transit.
- Key management notes: prefer external KMS/HSM equivalent; no private keys in tree.

## Still out of scope

- Live order routing, exchange API connectors, or withdrawal scopes.
- Storage of secrets, private keys, or personal data.
- Any claim of predictive edge, certified security, or investment advice.

See updated docs/asset-class-strategies.md and docs/security-architecture.md.
