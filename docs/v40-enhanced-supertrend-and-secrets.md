# v0.17 / v40: Supertrend proxy and expanded secret redaction

Research enhancement only. Still paper-only, no live execution, no trade keys.

## Strategy enhancements

- Added a simple Supertrend-style proxy (ATR-based bands with close relative to midpoint) as additional trend confirmation for Major, Large-cap alt, DeFi, and RWA classes.
- Used as a filter alongside existing ADX-style, CCI, Williams %R, and multi-factor checks.
- Volatility-scaled sizing remains; stress regime still forces flat.
- All rules remain transparent heuristics on synthetic fixtures.

## Cyber / data security enhancements

- Expanded SECRET_PATTERNS to include more JWT-like tokens, additional base58 variants, and common API token formats.
- Added notes on session-level zero-trust re-validation of source digests and indicator consistency (including new Supertrend proxy).
- Strengthened data residency attestation language.
- Redaction now covers more potential secret formats without changing the no-storage policy.

## Still out of scope

- Any live order routing or exchange connectors.
- Storage of secrets or personal data.
- Claims of future performance.

This continues the paper research harness under the existing controls.
