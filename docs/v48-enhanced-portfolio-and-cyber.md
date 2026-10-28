# v0.48 enhancements: portfolio-level risk aggregation, refined multi-factor strategies, and advanced zero-trust cyber architecture

Research only. Paper-only. Not financial, legal, or security advice.

## Strategy upgrades (per asset class + portfolio)

- **Portfolio-level risk aggregation**: New heuristic that computes a synthetic portfolio VaR-style proxy (historical simulation on recent returns across classes) and concentration HHI. High portfolio concentration or elevated joint stress reduces size across correlated classes (Large-cap, DeFi, L2, Meme). Majors retain higher base but still scale down.
- **Refined multi-factor confirmation**: Added simple momentum persistence score (fraction of positive returns in last N bars) and volume-profile proxy (recent volume vs longer average). Applied as additional filter on top of existing correlation, adaptive MTF, and indicator stack.
- **Class-specific refinements**:
  - Major: Portfolio concentration check; stand-aside if joint stress with alts exceeds threshold.
  - Large-cap alt: Require momentum persistence + relative volume vs major for breakout.
  - DeFi / L2: Prefer moderate correlation + positive momentum persistence; suppress on high portfolio HHI.
  - Meme: Burst now requires short momentum persistence and correlation decay; tighter size under portfolio stress.
  - Stablecoin / RWA / Perpetual: Portfolio stress overlay for alerts; no new directional size. RWA gap halt strengthened with portfolio context.
- **All classes**: Reasons list now includes portfolio risk status, momentum persistence, and concentration score for audit transparency. Shared stress overlay and previous filters retained.

All rules remain transparent heuristics on synthetic candles. No edge or future-return claim is made. Scores describe the fixture only.

## Cyber / data security upgrades

- Advanced zero-trust data plane: Source attestation now includes a simulated multi-party sealed digest (operator + auditor hash commitment) over fixture label + quality metrics + portfolio risk snapshot. Inputs must pass dual acknowledgment before strategy evaluation.
- Expanded redaction and classification: Explicit handling for portfolio-derived features as derived public data; additional patterns for hardware wallet QR fragments and multi-sig key shares (simulated).
- Simulated MPC-style key ceremony note for any future read-only credential (still refused for trade keys). Audit log records dual-control acknowledgments.
- Integrity enhancements: Portfolio risk jump detection as tertiary integrity signal; hash-chain retained with optional sealed multi-hash.
- Data residency stamp expanded to include portfolio computation lineage.

## Threat model additions

| Threat | Control |
|---|---|
| Correlated portfolio blow-up | Portfolio VaR proxy + concentration HHI + adaptive size |
| Single-point attestation failure | Simulated multi-party sealed digest + dual acknowledgment |
| Derived portfolio feature injection | Quality gate + multi-hash attestation before strategy |
| Partial multi-sig or HW wallet paste | Expanded redaction + gitleaks CI |
| Audit without dual review | Simulated dual-control for high-impact actions |

## Operating notes

- Still no order router, no trade/withdrawal keys, no live mode. `assert_paper_only` and `refuse_trade_secret` unchanged.
- Human dual review preferred before kill-switch clear or catalog changes.
- PDPA tripwire, gitleaks CI, paper-only constraints, and AI-disclosure trail unchanged.
- Inspired by the process in zeekiankok92/aixtech-agent-harness-demo.
- Promote any signal only via a separate, human-approved system.

See also docs/v47-enhanced-correlation-and-cyber.md and earlier version notes.
