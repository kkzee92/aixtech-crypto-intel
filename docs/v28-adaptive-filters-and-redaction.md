# Version 0.28: adaptive volatility/participation filters and expanded redaction

Research layer only. These changes tighten signal quality with ATR and multi-bar participation filters per asset class and expand secret redaction. They do not enable live orders, generate keys, open sockets, or change the paper-only invariant.

## Strategy enhancements per asset class

| Class | v0.28 addition | Effect |
|---|---|---|
| Major | ATR% filter (stand aside if average range > ~4% of price) + multi-TF volume | Reduces entries in elevated-volatility regimes |
| Large-cap alt | Volume threshold raised to 1.5x base + acceleration required | Stronger participation confirmation on breakouts |
| Stablecoin | Unchanged (monitor only) | Size remains zero |
| DeFi | Multi-bar volume trend (rising over 5 bars) in addition to calm vol | Extra participation confirmation |
| Meme | Liquidity floor raised to 3000; stricter extension and acceleration | Filters thinner or chasing spikes |
| L2 | Own ATR% not extreme + relative strength | Avoids high-volatility relative bets |
| RWA | Participation and low-vol checks strengthened | Prefers slow, participated trends |
| Perpetual | Funding persistence and drift containment unchanged; size caps held | Carry/fade remain research observations |

All prior regime, confirmation, sleeve, guard, book, cross-asset, and decay overlays remain in force. The core `signal_for` still proposes; downstream gates decide.

## Cyber and data-security enhancements

- Expanded `SECRET_PATTERNS` in `security.py`:
  - GitHub personal access tokens (`ghp_`, `github_pat_`)
  - Discord bot/user tokens
  - Additional high-entropy markers
- Additional classification rows for `github_pat` and `discord_token` (never stored, always redacted).
- Audit events continue to pass through expanded redaction before chaining.
- Integrity digest and paper-only guards unchanged.

## Operating rules (unchanged invariants)

- Paper-only. `assert_paper_only` still raises on any non-PAPER mode.
- No trade / withdrawal / order credential is accepted.
- No role can place an order or clear the kill switch alone.
- Synthetic or PUBLIC_READ labels only for fixtures.
- Scores describe the fixture, not future returns.

See also [security-architecture.md](security-architecture.md) and [asset-class-strategies.md](asset-class-strategies.md).
