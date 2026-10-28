# v0.46 enhancements: adaptive multi-timeframe filters, on-chain proxy heuristics, and zero-trust data plane

Research only. Paper-only. Not financial, legal, or security advice.

## Strategy upgrades (per asset class)

- **Adaptive multi-timeframe (MTF) consistency**: Strengthened multi-TF alignment check (short vs medium horizon EMAs or returns). Mismatch now more strictly suppresses directional signals across Major, Large-cap, DeFi, and L2. Used as additional confirmation filter.
- **On-chain proxy heuristics** (synthetic only): Volume concentration proxy and simple flow imbalance (rising vs falling volume bars) as lightweight confirmation. Applied to Major trend path, Large-cap breakouts, and Meme burst qualification. No real on-chain data is fetched; proxies derived from OHLCV fixtures.
- **Adaptive volatility scaling refinement**: Size fraction further scaled by recent ATR percentile within class. High ATR percentile reduces size even within class cap.
- **All classes**: Reasons include MTF alignment status and volume-flow proxy for transparency. Shared regime overlay and stress stand-aside unchanged.
- **Stablecoin / Perpetual / RWA**: Light adaptive filters retained; no new directional size introduced.

All rules remain transparent heuristics on synthetic candles. No edge or future-return claim is made. Scores describe the fixture only.

## Cyber / data security upgrades

- Zero-trust data plane notes: All inputs (fixture or injected) must pass source attestation + quality gate before strategy evaluation. Expanded residency stamp in audit events.
- Enhanced redaction for potential on-chain related strings (wallet-like, tx-hash-like patterns) even though none are used.
- Simulated multi-factor confirmation gate for research audit trail (operator + auditor dual acknowledgment for kill-switch clear).
- Data classification updated to explicitly ban any real on-chain address or transaction data in fixtures or logs.
- Catalog digest and hash-chain integrity retained; feed jump/staleness checks unchanged.

## Threat model additions

| Threat | Control |
|---|---|
| Real on-chain data injection | Synthetic label + attestation required; banned patterns |
| Weak MTF oversized risk | Adaptive MTF consistency filter |
| Volume-flow param injection | Source attestation |
| Audit without dual review | Simulated multi-factor note in logs |

## Operating notes

- Still no order router, no trade/withdrawal keys, no live mode. `assert_paper_only` unchanged.
- Human review required before any kill-switch clear. Dual acknowledgment preferred.
- PDPA tripwire, gitleaks CI, and paper-only constraints unchanged.
- Promote any signal only via a separate, human-approved system.

See also docs/v45-enhanced-bb-vwap-and-cyber.md and earlier version notes.
