# Version 0.29: adaptive correlation filters, dual-side research signals, and expanded secret patterns

Research layer only. These changes add cross-asset correlation awareness, limited dual-side (long/short) research signals for selected classes, and additional secret-pattern coverage. They do not enable live orders, generate keys, open sockets, or change the paper-only invariant.

## Strategy enhancements per asset class

| Class | v0.29 addition | Effect |
|---|---|---|
| Major | Dual-side: short when fast EMA below slow, RSI > 55, volume rising, outside stress; correlation check vs self | Allows paper short research in clear downtrends; reduces false longs |
| Large-cap alt | Correlation vs Major benchmark if supplied; volume acceleration retained | Filters breakouts that are purely beta |
| Stablecoin | Unchanged (monitor only) | Size remains zero |
| DeFi | Soft correlation filter vs Major (stand aside if highly correlated and Major in stress) | Reduces crowded DeFi risk |
| Meme | Unchanged core + liquidity/ATR ratio guard | Avoids extreme thin spikes |
| L2 | Stronger relative-strength + optional correlation decay | Prefers idiosyncratic strength |
| RWA | Unchanged slow-trend + participation | Continues to prefer low-vol |
| Perpetual | Dual-side funding fade/carry with persistence; size caps held | Research shorts on crowded funding remain |

All prior regime, confirmation, sleeve, guard, book, cross-asset, ATR, and decay overlays remain in force. The core `signal_for` still proposes; downstream gates decide.

## Cyber and data-security enhancements

- Expanded `SECRET_PATTERNS` in `security.py`:
  - OpenAI-style keys (`sk-`, `sk-proj-`)
  - Telegram bot tokens
  - Additional JWT and high-entropy variants
  - AWS session tokens (ASIA already partially covered)
- Additional classification rows for `openai_key` and `telegram_token` (never stored, always redacted).
- New helper `redact_mapping` for structured payloads (dict/list) before logging.
- Audit events continue to pass through expanded redaction before chaining.
- Integrity digest and paper-only guards unchanged.

## Operating rules (unchanged invariants)

- Paper-only. `assert_paper_only` still raises on any non-PAPER mode.
- No trade / withdrawal / order credential is accepted.
- No role can place an order or clear the kill switch alone.
- Synthetic or PUBLIC_READ labels only for fixtures.
- Scores describe the fixture, not future returns.

See also [security-architecture.md](security-architecture.md) and [asset-class-strategies.md](asset-class-strategies.md).
