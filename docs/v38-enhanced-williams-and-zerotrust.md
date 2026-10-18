# v0.15 Enhancement Log: Williams %R Confirmation, Enhanced Anomaly Scoring, and Zero-Trust Hardening

Version 0.15 adds the Williams %R oscillator as a fast momentum confirmation filter for Major and Large-cap alt strategies, refines anomaly scoring with extreme oscillator readings, and further hardens the cyber/data security architecture with explicit zero-trust and encryption notes.

All changes remain strictly paper-only research. No live execution paths exist.

## Strategy enhancements per asset class

- **Major**: Williams %R (14) contained between -80 and -20 required for trend entries alongside existing multi-factor stack (EMA, MACD-style, CCI, stochastic, BB, VWAP, adaptive RSI). Extreme readings outside this band suppress or reduce confidence. Range-mode mean-reversion still uses deep RSI/stochastic; %R oversold exit can boost confidence.
- **Large-cap alt**: Williams %R not in extreme overbought (above -20) required on breakout confirmation to avoid chasing exhausted moves. Combined with volume MAD, CCI, and strength filters.
- Adaptive confidence continues to scale with the number of confirming factors. Volatility-scaled sizing and class caps unchanged.
- Other classes retain prior filters; notes added for optional future %R extension on DeFi/RWA trend filters.

## Cyber and data security architecture

- Expanded SECRET_PATTERNS for additional private-key and seed-phrase proxies (longer hex, common mnemonic patterns).
- Anomaly scoring now incorporates Williams %R extremes and multi-oscillator divergence as feed-integrity signals.
- Explicit zero-trust re-validation on every scan: source attestation, series digest, audit chain, and oscillator consistency.
- Production research deployment notes strengthened: AES-256 at rest, TLS 1.3 in transit, key management via external HSM or KMS equivalent, just-in-time access, continuous monitoring of audit chain integrity.
- Continued: hash-chained audit logs, expanded redaction, paper-only PermissionError guards, PDPA tripwire, gitleaks in CI, no trader role.

## Still out of scope

- Live order routing, exchange API connectors, or withdrawal scopes.
- Storage of secrets, private keys, or personal data.
- Any claim of predictive edge, certified security, or investment advice.

See updated docs/asset-class-strategies.md and docs/security-architecture.md.
