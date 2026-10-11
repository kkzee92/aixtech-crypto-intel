# Version 0.27: multi-timeframe confirmation and integrity controls

Research layer only. These changes tighten signal quality and expand redaction/integrity. They do not enable live orders, generate keys, open sockets, or change the paper-only invariant.

## Strategy enhancements per asset class

| Class | v0.27 addition | Effect |
|---|---|---|
| Major | Multi-timeframe: 21-bar EMA must also be rising or flat | Reduces counter-trend entries on short EMA crossovers |
| Large-cap alt | Volume acceleration (current volume > 1.5× prior 3-bar average) | Stronger participation filter on breakouts |
| Stablecoin | Unchanged (monitor only) | Size remains zero |
| DeFi | Multi-timeframe calm check: 13-bar realised vol also ≤ 5% | Extra regime confirmation |
| Meme | Volume acceleration required on the burst bar | Filters low-participation spikes |
| L2 | Benchmark multi-timeframe: benchmark 8-bar return must be non-negative | Avoids relative strength in a declining benchmark |
| RWA | Gap and vol already strict; added low-volume confirmation | Prefers participation on slow trends |
| Perpetual | Funding carry now requires 3-bar funding persistence | Reduces one-bar noise |

All prior regime, confirmation, sleeve, guard, book, cross-asset, and decay overlays remain in force. The core `signal_for` still proposes; downstream gates decide.

## Cyber and data-security enhancements

- Expanded `SECRET_PATTERNS` in `security.py`:
  - JWT-style tokens (`eyJ...`)
  - Slack bot/user tokens (`xoxb-`, `xoxp-`)
  - Generic high-entropy base64-like secrets
- New `integrity_digest(payload)` helper that SHA-256-hashes a fixture or config body after redaction (for attestation).
- Audit events continue to pass through expanded redaction before chaining.
- Additional classification row for `jwt_token` and `slack_token` (never stored, always redacted).

## Operating rules (unchanged invariants)

- Paper-only. `assert_paper_only` still raises on any non-PAPER mode.
- No trade / withdrawal / order credential is accepted.
- No role can place an order or clear the kill switch alone.
- Synthetic or PUBLIC_READ labels only for fixtures.
- Scores describe the fixture, not future returns.

See also [security-architecture.md](security-architecture.md) and [asset-class-strategies.md](asset-class-strategies.md).
