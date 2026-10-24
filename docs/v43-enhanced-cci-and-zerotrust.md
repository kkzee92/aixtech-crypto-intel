# v0.43 Enhancements: CCI proxy and zero-trust refinements

Version 0.43 builds on the v0.42 multi-factor, MACD, and multi-TF framework.

## Strategy updates

- Added a simple CCI (Commodity Channel Index) proxy for additional mean-reversion and overbought/oversold confirmation in Major and DeFi classes.
- CCI > +100 or < -100 can invalidate or confirm depending on regime (research heuristic only).
- Adaptive size reduction when short-term ATR exceeds class-specific stress band (feeds into risk gate).
- PLAYBOOK entries updated for transparency.

## Security / cyber updates

- Expanded SECRET_PATTERNS with additional hardware-wallet and exchange-specific token formats.
- AuditLog now optionally flags consecutive-action bursts above a threshold as anomaly notes in the stamp.
- Strengthened zero-trust input attestation: integrity_digest now recommended on all external fixtures.
- Data classification table extended for "session_lineage" and "anomaly_flag".

These remain research controls. No live execution path is added.

## Still out of scope

- Live order routing, withdrawal, trade API keys.
- Certified security product claims.
- Guaranteed returns. Scores describe synthetic fixtures.
