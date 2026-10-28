# v0.45 enhancements: Bollinger Band proxy, volume profile, adaptive clustering, and entropy anomaly detection

Research only. Paper-only. Not financial, legal, or security advice.

## Strategy upgrades (per asset class)

- **Bollinger Band proxy**: 20-bar mean ± 2 std dev for major range reversion and large-cap breakout confirmation. Price outside upper band suppresses long in range; lower band supports reversion.
- **Volume profile proxy**: Compare recent volume to 20-bar average and distribution skew for confirmation on breakouts and memes. High relative volume required for large-cap and meme.
- **Adaptive volatility clustering**: Simple stddev of returns over 8/20 bars to scale confidence per class (majors more tolerant).
- **All classes**: Regime overlay retained; new filters applied to major, large-cap, meme, and DeFi where relevant.
- Reasons updated for transparency including BB position and vol profile.

All rules remain transparent heuristics on synthetic candles. No edge or future-return claim is made.

## Cyber / data security upgrades

- New entropy check function for anomaly detection on payloads (high entropy flags potential secrets or noise).
- Expanded SECRET_PATTERNS for additional API key formats (e.g., longer tokens, base64-like).
- AuditLog supports optional entropy flag in stamps for zero-trust monitoring.
- Isolation simulation: residency and consecutive counters strengthened with entropy tag.
- Classification updated for entropy-sensitive fields.

## Threat model additions

| Threat | Control |
|---|---|
| High-entropy secret paste | Entropy threshold check before redaction |
| Weak-volume breakout | Volume profile confirmation |
| Range-bound BB ignore | Bollinger position filter |
| Audit noise injection | Entropy stamp in chain |

## Operating notes

- Still no order router, no trade/withdrawal keys, no live mode. `assert_paper_only` unchanged.
- Human review required before any kill-switch clear.
- PDPA tripwire and gitleaks CI unchanged.
- Promote any signal only via a separate, human-approved system.

See also docs/v44-enhanced-ichimoku-and-cyber.md and earlier version notes.
