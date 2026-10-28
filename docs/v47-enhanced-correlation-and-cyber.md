# v0.47 enhancements: cross-asset correlation filters, refined adaptive strategies, and strengthened zero-trust cyber architecture

Research only. Paper-only. Not financial, legal, or security advice.

## Strategy upgrades (per asset class)

- **Cross-asset correlation filter**: New heuristic that measures short-horizon return correlation versus a major benchmark (synthetic BTC proxy). Extreme positive correlation during stress suppresses directional size across Large-cap, DeFi, L2, and Meme. Negative correlation can allow selective relative strength. Applied as additional confirmation layer on top of existing multi-factor and adaptive MTF.
- **Refined adaptive volatility and regime**: Size scaling now incorporates both ATR percentile and a multi-horizon regime consistency score (short vs medium). Inconsistent regimes reduce confidence further.
- **Class-specific refinements**:
  - Major: Correlation-adjusted sizing; stand-aside if self-correlation breaks in stress.
  - Large-cap alt: Relative volume vs major benchmark required for breakout confirmation.
  - DeFi / L2: Prefer signals when correlation to major is moderate (not extreme).
  - Meme: Burst qualification now requires correlation decay after initial spike.
  - Stablecoin / RWA / Perpetual: Light correlation monitoring retained for alerts only; no new directional size.
- **All classes**: Reasons list now includes correlation status, multi-horizon regime score, and adaptive filter outcomes for audit transparency. Shared stress overlay unchanged.

All rules remain transparent heuristics on synthetic candles. No edge or future-return claim is made. Scores describe the fixture only.

## Cyber / data security upgrades

- Strengthened zero-trust data plane: Source attestation now includes a simulated multi-hash sealed digest over the fixture label + quality metrics + correlation proxy snapshot. Inputs must pass before any strategy evaluation.
- Expanded redaction patterns: Additional coverage for partial seed phrases, hardware wallet export fragments, and session token patterns, even though none are present.
- Simulated dual-control for high-impact actions (kill-switch clear, catalog changes) with operator + auditor acknowledgment note in the audit log.
- Data classification updated to explicitly treat correlation-derived features as derived public market data (still synthetic-only in this repo).
- Feed integrity and hash-chain retained; added correlation-jump detection as a secondary integrity signal.

## Threat model additions

| Threat | Control |
|---|---|
| Correlation manipulation via fixture | Source attestation + synthetic label + multi-hash |
| Oversized correlated risk in stress | Cross-asset correlation filter + adaptive size |
| Partial secret paste (seed fragment) | Expanded redaction + gitleaks CI |
| Audit without dual review on kill-switch | Simulated multi-factor acknowledgment |
| Derived feature injection | Quality gate + attestation before strategy |

## Operating notes

- Still no order router, no trade/withdrawal keys, no live mode. `assert_paper_only` and `refuse_trade_secret` unchanged.
- Human review required before any kill-switch clear. Dual acknowledgment preferred.
- PDPA tripwire, gitleaks CI, paper-only constraints, and AI-disclosure trail unchanged.
- Inspired by the process in zeekiankok92/aixtech-agent-harness-demo.
- Promote any signal only via a separate, human-approved system.

See also docs/v46-enhanced-adaptive-mtf-and-cyber.md and earlier version notes.
