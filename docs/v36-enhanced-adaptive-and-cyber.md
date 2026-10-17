# v0.12 Enhancement Log: Adaptive Filters, Robust Volume Profiles, and Expanded Cyber Controls

Version 0.12 builds on v0.11 with more adaptive research filters per asset class, robust volume statistics, multi-timeframe alignment expanded to additional classes, and strengthened cyber/data security patterns and integrity checks.
All changes remain paper-only and research-oriented. No live execution.

## Strategy enhancements per asset class

- Expanded multi-timeframe (MTF) slope alignment proxy to DeFi and RWA trend entries (short vs medium window).
- Robust volume profile: median + simple IQR proxy for thin-print and outlier detection across classes (especially Meme, Large-cap alt, DeFi).
- Simple support/resistance proxy (recent swing high/low) for confirmation on Major and Large-cap alt breakouts.
- Adaptive confidence scoring based on number of confirming factors (research heuristic).
- Perpetual carry adds funding trend consistency check over longer window.
- Volatility scaling, regime overlays, class caps, costs, and horizons preserved in principle.

## Cyber and data security architecture

- Additional SECRET_PATTERNS for common crypto private key formats (longer base58, WIF-style proxies) and API token variants.
- Enhanced series integrity: optional rolling digest over last N candles for anomaly detection.
- Anomaly scoring refined with volume outlier and funding jump components.
- Reinforced zero-trust re-validation of source attestations, series digests, and audit chain on every operation.
- Notes on production research store: encryption at rest, access logging, and data residency preferences (local preferred).
- Continued hash-chained audit, expanded redaction, paper-only guards, PDPA tripwire, and key separation.

## Still out of scope

- Live order routing, exchange connectors, or withdrawal paths.
- Storage of any secrets or personal data.
- Claims of predictive performance or certified security.

See updated docs/asset-class-strategies.md and docs/security-architecture.md for full details.
