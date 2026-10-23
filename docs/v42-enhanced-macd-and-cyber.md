# v0.42 enhancements: MACD-style momentum confirmation and strengthened cyber controls

Research only. Paper-only. Not financial, legal, or security advice.

## Strategy upgrades (per asset class)

- **MACD-style proxy**: Simple 12/26 EMA difference histogram confirmation added to major trend and large-cap breakout entries. Requires positive histogram for long signals in addition to existing multi-factor and strength filters.
- **Multi-timeframe consistency**: Longer-window (20-bar) trend alignment check for majors. Entries prefer alignment with the slower trend direction.
- **Adaptive scaling**: Refined so extreme volatility further reduces size; baseline uses 16-bar window.
- **Meme / Perpetual**: Retained volume-spike and funding-flip logic with shared adaptive overlay.
- **All classes**: Reasons now include MACD histogram proxy and multi-TF flag for transparency.

All rules remain transparent heuristics on synthetic candles. No edge or future-return claim is made.

## Cyber / data security upgrades

- Expanded `SECRET_PATTERNS`: JWT-like tokens (three base64 segments), additional cloud provider key prefixes, and tighter private-key hex length variants.
- AuditLog append now includes a simple consecutive-action counter in the stamp for basic anomaly visibility.
- New classification entry for JWT / bearer tokens.
- `integrity_digest` remains the zero-trust input gate.
- Redaction applied before any stamp or chain append.

## Threat model additions

| Threat | Control |
|---|---|
| JWT or bearer token paste | Additional regex pattern + contains_secret |
| Rapid successive signals (spam) | Consecutive counter in audit stamp |
| MACD parameter injection | Source attestation + synthetic label still required |
| Extreme-vol oversized risk | Refined adaptive scale in strategy and risk gate |

## Operating notes

- Still no order router, no trade/withdrawal keys, no live mode. `assert_paper_only` unchanged.
- Human review required before any kill-switch clear.
- PDPA tripwire and gitleaks CI unchanged.
- Promote any signal only via a separate, human-approved system.

See also docs/v41-enhanced-adaptive-and-cyber.md and earlier version notes.
