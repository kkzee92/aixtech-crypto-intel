# v0.49 Enhanced Strategies and Cyber/Data Security Architecture

## Overview
This v0.49 enhancement refines multi-factor confirmation per asset class and strengthens the zero-trust control plane. Adaptive filters are tighter, volume and correlation gates are more explicit, and audit anomaly detection is expanded. Research only — no live execution.

**Disclaimer:** Not financial advice. Paper-only information system.

## Asset-Class Strategy Enhancements

### Major (BTC/ETH)
- Tighter multi-TF: requires 5/13 EMA alignment **and** 20-bar SMA slope positive.
- Adaptive RSI band: widens to 40-75 in low-vol (ATR% < 2%), tightens to 48-68 in high-vol.
- Correlation stand-aside if pairwise corr > 0.82 with the other major during elevated ATR.

### Large-cap Alts
- Relative volume vs major proxy must exceed 1.6x for breakout confirmation.
- BB squeeze preferred; expansion without volume now invalidates.

### DeFi
- Calm regime tightened: 8-bar realised vol < 3.5% **and** ADX > 20.
- Volume-flow proxy + above VWAP required.

### Meme
- Chase filter hardened: 8-bar extension < 25%.
- Correlation decay vs BTC: stand aside if rolling corr > 0.65.

### L2 / RWA / Perpetual
- L2: multi-TF relative strength + volume confirmation vs benchmark.
- RWA: added slow MACD histogram > 0 for trend confirmation.
- Perpetual: funding flip (sign change within 3 bars) raises elevated alert.

## Cyber and Data Security Updates

### Expanded Controls
| Control | Description | Status |
|---------|-------------|--------|
| Consecutive action anomaly | Flags >5 identical actions in a row in audit log | New |
| Additional redaction | Cosmos/Terra-style keys, extended hardware export patterns | Enhanced |
| Multi-hash sealed lineage | Optional SHA-256 + SHA-512 prefix on critical events | Active |
| Correlation jump signal | Risk gate monitors sudden cross-asset corr spikes | Strengthened |
| Residency + consecutive stamp | Combined in every audit event | Maintained |

### Zero-Trust Principles Maintained
- Source attestation mandatory (SYNTHETIC / PUBLIC_READ).
- No live order path; RBAC denies all trade roles.
- Kill switch + drawdown halt + class caps remain hard gates.
- PDPA tripwire + gitleaks continue to protect fixtures and docs.

### Recommendations
1. Keep research and any future execution systems fully segregated.
2. Rotate any optional read-only market keys outside the repo via external KMS.
3. Human review required before clearing kill switch.
4. Continue expanding secret patterns as new wallet formats appear.

## Implementation Notes
- Heuristics remain transparent and paper-only.
- Inspired by the AI-agent harness process in zeekiankok92/aixtech-agent-harness-demo.
- Next: integrate the adaptive RSI and consecutive anomaly into core modules and expand tests.
