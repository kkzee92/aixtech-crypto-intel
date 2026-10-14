# Version 0.5 enhancement summary

Paper-only research harness update. No live trading capability was added.

## Strategy enhancements (per asset class)

- **Major**: MACD-style histogram confirmation required for trend entries; deeper RSI washout for mean-reversion.
- **Large-cap alt**: Volume threshold raised to 1.4x; follow-through bar required.
- **Stablecoin**: Watch and depeg thresholds tightened slightly for earlier monitoring.
- **DeFi**: Calm-regime realised-vol cutoff tightened to 5.5%.
- **Meme**: Burst window shortened to 3 bars at 12%; extension filter tightened to 30%; higher volume floor.
- **L2**: Relative-strength threshold raised to 3.5%; tighter ATR containment.
- **RWA**: Gap halt tightened to 7%; stronger momentum confirmation.
- **Perpetual**: Crowded-funding alert lowered to 8 bps; drift containment tightened to 3.5%.

All directional signals remain vol-scaled and subject to the existing risk gate.

## Cyber and data-security enhancements

- Expanded redaction patterns: mnemonic keywords, additional key prefixes, raw 64-hex private-key proxies.
- Data classification notes updated with encryption-at-rest guidance for any future persisted secrets or audit details.
- Added `derive_research_key` research stub (SHA-256 of passphrase) for documenting optional encryption of audit material. Explicitly not a production KDF.
- Security architecture diagram and threat table updated.

## Honesty

Scores and backtests remain descriptions of synthetic fixtures only. No exchange secrets are loaded. Promoting any signal to a live broker remains outside this system and requires separate human-approved controls.
