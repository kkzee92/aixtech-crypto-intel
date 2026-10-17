# v0.11 Enhancement Log: Multi-Timeframe Proxies, Expanded Cyber Patterns, and Resilience

Version 0.11 builds on v0.10 with research multi-timeframe alignment proxies, additional secret redaction patterns for common crypto formats, improved anomaly components, and reinforced data resilience notes.
All changes remain paper-only and research-oriented. No live execution.

## Strategy enhancements per asset class

- Added simple multi-timeframe (MTF) confirmation proxy: short-window (e.g. 5-bar) slope aligned with longer (e.g. 13-bar) for Major and Large-cap alt trend entries.
- Refined volume profile proxy using median + IQR-like robustness for thin-print detection across classes.
- Enhanced L2 relative strength with optional multi-window excess return check.
- Perpetual carry refined with funding rate trend proxy (recent prints direction).
- Volatility scaling and regime overlays unchanged in principle; size remains vol-scaled.
- Asset class caps, costs, and horizons preserved.

## Cyber and data security architecture

- Expanded SECRET_PATTERNS with additional Solana-style base58 private key proxies and longer hex (128-char) styles.
- Enhanced anomaly_score with optional funding rate jump component for perpetual series.
- Added notes on log encryption at rest (AES-256 recommended for production research stores) and data residency (prefer local or compliant cloud; no personal data).
- Reinforced zero-trust: independent re-validation of all series digests and source attestations on every scan.
- Continued hash-chained audit, expanded redaction (including prior patterns), sanitization, paper-only guards, and PDPA tripwire.
- Key separation and no-withdrawal scope unchanged.

## Still out of scope

- Live order routing, exchange connectors, or withdrawal paths.
- Storage of any secrets or personal data.
- Claims of predictive performance or certified security.

See updated docs/asset-class-strategies.md and docs/security-architecture.md for full details.
