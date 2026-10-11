# Version 0.26: enhanced strategies and cyber/data security

Research layer only. These changes tighten information quality and redaction. They do not enable live orders, generate keys, or open sockets.

## Strategy enhancements per asset class

| Class | v0.26 addition | Effect |
|---|---|---|
| Major | Rising-volume confirmation on EMA trend | Reduces false breaks; confidence slightly higher |
| Large-cap alt | RSI < 75 guard on breakout | Avoids overbought chase |
| Stablecoin | Unchanged (monitor only) | Size remains zero |
| DeFi | Rising-volume filter on calm trend | Stands aside on weak participation |
| Meme | Liquidity floor raised to 2000 | Tighter thin-book rejection |
| L2 | Absolute six-bar return must be positive | Requires both relative and absolute strength |
| RWA | Realised-vol ceiling of 3% | Halts elevated-volatility slow trends |
| Perpetual | Unchanged core (carry + crowded fade) | Existing paper short retained |

All prior regime, confirmation, sleeve, guard, book, and cross-asset overlays remain in force. The core `signal_for` still proposes; downstream gates decide.

## Cyber and data-security enhancements

- Expanded `SECRET_PATTERNS` in `security.py`:
  - Mnemonic / seed phrase / private key / xprv / xpub markers
  - 64-character hex strings (raw private-key shape)
  - AWS-style access-key prefixes
- Additional classification rows for mnemonic and private_key (never stored, always redacted).
- `redact` and `contains_secret` now cover the wider set.
- Audit chain continues to run every detail through redaction before hashing.

## Operating rules (unchanged invariants)

- Paper-only. `assert_paper_only` still raises on any non-PAPER mode.
- No trade / withdrawal / order credential is accepted.
- No role can place an order or clear the kill switch alone.
- Synthetic or PUBLIC_READ labels only for fixtures.
- Scores describe the fixture, not future returns.

See also [security-architecture.md](security-architecture.md) and [asset-class-strategies.md](asset-class-strategies.md).
