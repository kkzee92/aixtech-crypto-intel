# v0.41 enhancements: adaptive volatility strategies and strengthened cyber controls

Research only. Paper-only. Not financial, legal, or security advice.

## Strategy upgrades (per asset class)

- **Adaptive scaling**: Confidence and proposed size lightly scaled by current ATR relative to an 8-bar baseline. High-vol environments reduce size without changing the core heuristic.
- **Major / Large-cap Alt**: Added simple ADX-style trend-strength proxy (directional movement ratio). Trend entries require strength above a threshold in addition to multi-factor EMA/RSI/volume/BB.
- **Meme**: Volume-spike filter versus longer (10-bar) average; stricter chase filter.
- **Perpetual**: Funding-trend awareness (current vs prior bar) so a sudden funding flip raises an alert even if absolute level is mild.
- **DeFi / RWA / L2**: Retained prior rules with the shared adaptive overlay.
- Reasons now include the adaptive factor for transparency.

All rules remain transparent heuristics on synthetic candles. No edge or future-return claim is made.

## Cyber / data security upgrades

- Expanded `SECRET_PATTERNS`: Solana-style base58 private keys, additional raw hex variants, and tighter mnemonic detection.
- AuditLog append now supports a `sealed` flag that stores only a digest of the detail (simulated sealed lineage) while still chaining the hash.
- New classification entries for exchange session tokens and hardware-wallet seeds.
- `integrity_digest` reinforced as a zero-trust gate; callers should attest before strategy evaluation.
- Redaction remains mandatory and is applied before any stamp or chain append.

## Threat model additions

| Threat | Control |
|---|---|
| Solana or other private-key paste | Additional regex patterns + contains_secret |
| Detail leakage in audit | Optional sealed mode stores digest only |
| Adaptive parameter injection | Source attestation + synthetic label still required |
| Volatility-driven oversized risk | Adaptive scale in both strategy confidence and risk gate |

## Operating notes

- Still no order router, no trade/withdrawal keys, no live mode. `assert_paper_only` unchanged.
- Human review required before any kill-switch clear.
- PDPA tripwire and gitleaks CI unchanged.
- Promote any signal only via a separate, human-approved system.

See also docs/v40-enhanced-strategies-and-security.md and earlier version notes.
