# v0.43 enhancements: Supertrend-style confirmation and strengthened zero-trust controls

Research only. Paper-only. Not financial, legal, or security advice.

## Strategy upgrades (per asset class)

- **Supertrend-style proxy**: ATR-based trailing stop direction proxy added to major and large-cap entries. Requires price above the trailing band for long signals, combined with existing MACD, multi-TF, and adaptive filters.
- **Stochastic oscillator proxy**: %K/%D for range reversion in majors and calm regimes in DeFi. Oversold confirmation preferred for mean-reversion.
- **Adaptive scaling refined**: Incorporates Supertrend distance as additional vol factor.
- **Meme / Perpetual / L2 / RWA**: Shared overlay now includes optional Supertrend alignment where applicable.
- **All classes**: Reasons include Supertrend direction and Stochastic values for transparency.

All rules remain transparent heuristics on synthetic candles. No edge or future-return claim is made.

## Cyber / data security upgrades

- Expanded SECRET_PATTERNS for additional seed phrase variants and hardware wallet export formats.
- AuditLog supports optional encrypted-lineage simulation via integrity_digest wrapping.
- New classification for hardware wallet exports and session cookies.
- Zero-trust input gate strengthened with multi-hash attestation option.
- Redaction applied before any stamp or chain append; consecutive counter retained.

## Threat model additions

| Threat | Control |
|---|---|
| Hardware wallet seed paste | Expanded BIP39-like and export patterns |
| Supertrend param injection | Source attestation + synthetic label required |
| Extreme-vol oversized risk | Supertrend distance in adaptive scale |
| Session cookie in logs | Additional pattern + redaction |

## Operating notes

- Still no order router, no trade/withdrawal keys, no live mode. `assert_paper_only` unchanged.
- Human review required before any kill-switch clear.
- PDPA tripwire and gitleaks CI unchanged.
- Promote any signal only via a separate, human-approved system.

See also docs/v42-enhanced-macd-and-cyber.md and earlier version notes.
