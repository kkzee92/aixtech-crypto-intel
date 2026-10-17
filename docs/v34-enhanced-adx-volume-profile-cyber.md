# v0.10 Enhancement Log: ADX-Style Trend Strength, Volume Profile Proxies, and Cyber Hardening

Version 0.10 builds on v0.9 with additional research factors for better trend quality filtering and security controls.
All changes remain paper-only and research-oriented. Not financial advice.

## Strategy enhancements

- Added ADX-style directional movement proxy (simplified +DI/-DI difference normalized) across directional classes for stronger trend confirmation vs range.
- Introduced simple volume profile / OBV-style cumulative volume direction proxy to filter breakouts and trends with participation.
- Strengthened multi-window confirmation and adaptive thresholds using the new proxies.
- Refined L2 correlation and relative strength with volume-weighted elements where applicable.
- Volatility scaling, regime overlays, stochastic, MACD, BB, median volume, and prior factors retained.

## Security and data architecture

- Expanded SECRET_PATTERNS for additional cloud provider styles (Azure, generic high-entropy tokens).
- Enhanced anomaly_score with volume-profile deviation component.
- Added series_volume_integrity helper for research attestation of volume consistency.
- Reinforced zero-trust and key separation notes: market-data credentials (if ever) must be strictly read-only, rotated independently, and never co-located with any future trade credential.
- Continued hash-chained audit, redaction (including new patterns), sanitization, and PDPA tripwires.

## Still out of scope

- Live order routing, withdrawal, or exchange connectors.
- Storage of any secrets or personal data.
- Claims of predictive performance or future returns. Scores describe the synthetic fixture only.

See updated docs/asset-class-strategies.md and docs/security-architecture.md for full details.
