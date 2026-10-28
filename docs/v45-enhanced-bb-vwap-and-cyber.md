# v0.45 enhancements: Bollinger Band squeeze, VWAP proxy, and expanded secret redaction

Research only. Paper-only. Not financial, legal, or security advice.

## Strategy upgrades (per asset class)

- **Bollinger Band width proxy**: 20-bar BB width (std/mean) to detect squeeze (low width) vs expansion. Squeeze preferred for major range reversion; expansion filters weak breakouts in large-cap.
- **VWAP proxy**: Volume-weighted average price over recent bars for confirmation. Price above VWAP preferred for trend/breakout longs; used in major, large-cap, DeFi, and L2.
- **Consistent volume and ADX overlays**: Applied more uniformly to L2, RWA, and Perpetual for better quality filtering.
- **All classes**: Reasons now include BB width status and VWAP relation for transparency. Shared regime overlay unchanged.
- **Meme / Stablecoin**: Light volume confirmation retained; no new directional size.

All rules remain transparent heuristics on synthetic candles. No edge or future-return claim is made.

## Cyber / data security upgrades

- Expanded SECRET_PATTERNS for Solana private keys (base58-like), additional BIP39 variants, and common API secret formats.
- New classification for Solana key material and extended wallet exports.
- Redaction strengthened for potential base58 secrets and long alphanumeric strings resembling keys.
- AuditLog residency and multi-hash seals retained; zero-trust input gate notes updated.
- Simulated key-rotation attestation helper added for research logs.

## Threat model additions

| Threat | Control |
|---|---|
| Solana private key paste | Additional base58 pattern |
| BB/VWAP param injection | Source attestation + synthetic label required |
| Weak-volume oversized risk | VWAP and volume confirmation filters |
| Extended wallet backup | Expanded export patterns |

## Operating notes

- Still no order router, no trade/withdrawal keys, no live mode. `assert_paper_only` unchanged.
- Human review required before any kill-switch clear.
- PDPA tripwire and gitleaks CI unchanged.
- Promote any signal only via a separate, human-approved system.

See also docs/v44-enhanced-ichimoku-and-cyber.md and earlier version notes.
