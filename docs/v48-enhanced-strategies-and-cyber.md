# v0.48 Enhanced Strategies and Cyber/Data Security Architecture

## Overview
This enhancement builds on the existing paper-only research harness by refining asset-class specific trading strategies and strengthening the cyber and data security architecture. Focus is on adaptive multi-factor confirmation, improved risk gates, and expanded threat modeling for production-like research environments.

**Disclaimer:** Research only. Not financial advice. No live trading capabilities.

## Asset-Class Strategy Enhancements

### Major (BTC/ETH)
- Added adaptive volatility scaling: position size reduced by 30% if ATR% > 3.5%.
- Multi-TF consistency check: requires alignment on 5-bar and 13-bar EMAs plus 20-bar SMA.
- Correlation filter: stand aside if correlation with ETH (or BTC) > 0.85 during stress.

### Large-cap Alts
- Volume confirmation now requires relative volume vs major index proxy > 1.5x.
- Added BB squeeze breakout preference.

### DeFi
- Enhanced calm regime: realized vol < 4% over 8 bars AND ADX > 18.
- VWAP + volume-flow proxy required.

### Meme
- Added correlation decay check vs BTC; stand aside if corr > 0.7.
- Harder chase filter: 8-bar extension < 30%.

### L2 / RWA / Perpetual
- L2: multi-TF relative strength vs benchmark.
- RWA: added slow MACD confirmation.
- Perpetual: funding flip detection for alerts.

## Cyber and Data Security Updates

### Expanded Threat Model
| Threat | Control | Status |
|--------|---------|--------|
| Key leakage via logs | Expanded redaction (BIP39, Solana, session tokens, hardware wallet exports) | Enhanced |
| Fixture tampering | Multi-hash source attestation + lineage stamp | Active |
| Correlation jump attacks | Cross-asset correlation monitoring in risk gate | New |
| Residency violation | Data residency stamp in audit log | Active |
| Privilege escalation | No live order path; RBAC enforced | Maintained |

### Zero-Trust Principles
- All data sources must be attested (SYNTHETIC or PUBLIC_READ).
- Audit log is hash-chained with consecutive action counters.
- Kill switch and drawdown halt remain mandatory.
- PDPA tripwire expanded for more PII patterns.

### Recommendations for Production
1. External KMS for any read-only keys (never store in repo).
2. Separate research vs execution systems.
3. Regular secret scanning (gitleaks + custom patterns).
4. Human review for any kill-switch clear.

## Implementation Notes
- Strategies remain transparent heuristics.
- All changes are paper-only.
- Inspired by the AI-agent harness in zeekiankok92/aixtech-agent-harness-demo.

Next steps: integrate adaptive filters into `strategies.py` and update tests.
