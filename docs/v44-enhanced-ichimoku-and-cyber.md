# v0.44 enhancements: Ichimoku cloud proxy, ADX confirmation, RSI divergence, and strengthened zero-trust residency

Research only. Paper-only. Not financial, legal, or security advice.

## Strategy upgrades (per asset class)

- **Ichimoku cloud proxy**: Tenkan (9-bar mean) and Kijun (26-bar mean) direction for major and large-cap entries. Bullish required for trend/breakout confirmation alongside Supertrend and MACD.
- **ADX trend-strength proxy**: Simplified directional movement ADX approximation. Minimum threshold (>20 for majors, >15 for DeFi) to filter weak trends.
- **RSI divergence detection**: Simple 10-bar price vs RSI comparison for bullish/bearish divergence on mean-reversion and trend invalidation.
- **Adaptive overlays refined**: Reasons now include Ichimoku direction, ADX value, and divergence status for full transparency.
- **All classes**: Shared regime overlay unchanged; new indicators applied where relevant (majors, large-cap, DeFi).

All rules remain transparent heuristics on synthetic candles. No edge or future-return claim is made.

## Cyber / data security upgrades

- Expanded SECRET_PATTERNS for hardware export formats and additional seed variants.
- New classification for BIP39 seeds.
- AuditLog append supports optional region for simulated data residency stamp.
- Multi-hash sealed lineage retained; residency tag added to every stamp.
- Zero-trust input gate strengthened with residency-aware lineage.

## Threat model additions

| Threat | Control |
|---|---|
| Hardware wallet export paste | Expanded pattern for exports and backups |
| Weak-trend oversized risk | ADX threshold filter |
| Divergence-ignored entry | RSI divergence check on reversion |
| Cross-region data leak simulation | Residency stamp in audit chain |

## Operating notes

- Still no order router, no trade/withdrawal keys, no live mode. `assert_paper_only` unchanged.
- Human review required before any kill-switch clear.
- PDPA tripwire and gitleaks CI unchanged.
- Promote any signal only via a separate, human-approved system.

See also docs/v43-enhanced-supertrend-and-cyber.md and earlier version notes.
