# v0.45 enhancements: Bollinger Bands proxy, volume confirmation, and strengthened cyber controls

Research only. Paper-only. Not financial, legal, or security advice.

## Strategy upgrades (per asset class)

- **Bollinger Bands proxy**: 20-bar SMA ±2 stddev position check. For majors and large-cap: prefer entries not extended beyond upper band in trend mode; mean-reversion when near lower in range. Squeeze detection (bandwidth < recent avg) for breakout confirmation.
- **Refined volume filters**: Require volume > 1.1x recent average for trend/breakout paths; stronger spike (1.3x) for meme and large-cap.
- **Integration**: BB position and volume now annotated in signal reasons alongside existing Ichimoku, ADX, RSI divergence.
- **All classes**: Shared regime overlay unchanged; BB applied to major, large-cap, DeFi where volatility context helps.

All rules remain transparent heuristics on synthetic candles. No edge or future-return claim is made. See academic notes on regime-dependent BB efficacy.

## Cyber / data security upgrades

- Additional SECRET_PATTERNS for common exchange API key prefixes and private key hex variants.
- New `detect_audit_anomaly` helper: flags high consecutive identical actions as potential automation abuse simulation.
- AuditLog append now optionally records volume/BB context in research lineage stamps.
- Zero-trust input gate notes expanded for volatility-derived features.

## Threat model additions

| Threat | Control |
|---|---|
| Extended price entry (band walk) | BB upper-band filter on trend signals |
| Thin-volume false breakout | Stricter volume multiplier |
| Audit log flooding | Consecutive-action anomaly flag |
| Exchange key paste | Expanded prefix patterns |

## Operating notes

- Still no order router, no trade/withdrawal keys, no live mode. `assert_paper_only` unchanged.
- Human review required before any kill-switch clear.
- PDPA tripwire and gitleaks CI unchanged.
- Promote any signal only via a separate, human-approved system.

See also docs/v44-enhanced-ichimoku-and-cyber.md and earlier version notes.
