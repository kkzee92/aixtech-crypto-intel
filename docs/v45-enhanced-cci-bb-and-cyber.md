# v0.45 enhancements: CCI proxy, Bollinger Band squeeze filter, and strengthened data residency controls

Research only. Paper-only. Not financial, legal, or security advice.

## Strategy upgrades (per asset class)

- **CCI proxy**: Simplified Commodity Channel Index approximation using SMA and mean absolute deviation. Positive CCI required for trend/breakout confirmation on majors, large-cap alts, and DeFi; oversold CCI aids mean-reversion on majors.
- **Bollinger Band squeeze detection**: Current bandwidth vs recent average. Suppresses trend and breakout signals during low-volatility squeeze periods to avoid false breakouts; awaits expansion.
- **Volume confirmation refined**: Existing volume checks retained and cross-referenced with new filters for transparency.
- **All classes**: Shared regime overlay unchanged; new indicators applied where relevant (majors, large-cap, DeFi). Adaptive volatility scaling continues.

All rules remain transparent heuristics on synthetic candles. No edge or future-return claim is made. Scores describe the fixture only.

## Cyber / data security upgrades

- AuditLog residency stamp retained and noted for multi-region simulation.
- Expanded redaction patterns continue to cover hardware exports, BIP39 seeds, and session tokens.
- Zero-trust input gate: source attestation plus residency-aware lineage on every event.
- Data classification updated to emphasize synthetic-only fixtures and prohibited personal data.
- New control note: BB squeeze and CCI filters act as additional risk gates against weak or compressed-volatility entries.

## Threat model additions

| Threat | Control |
|---|---|
| False breakout in low-vol regime | BB squeeze filter suppresses entry |
| Weak momentum confirmation | CCI threshold on trend paths |
| Cross-region data residency mismatch | Residency stamp in audit chain |
| Secret-like strings in research logs | Expanded redaction + PDPA tripwire |

## Operating notes

- Still no order router, no trade/withdrawal keys, no live mode. `assert_paper_only` unchanged.
- Human review required before any kill-switch clear.
- PDPA tripwire and gitleaks CI unchanged.
- Promote any signal only via a separate, human-approved system.
- Version bump to 0.45.0 in pyproject and README.

See also docs/v44-enhanced-ichimoku-and-cyber.md and earlier version notes.
