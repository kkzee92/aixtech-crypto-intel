# Version 0.6 class enhancements and cyber layer

Paper research only. These rules cannot raise a class cap, create a key, open a
socket, or place an order.

## Per-class enhancement

`crypto-intel enhance` runs after the v0.4 information path.

| Class | Enhancement | Effect |
|---|---|---|
| Major | Realised-vol dampener above 4% mean absolute return | Paper size halved |
| Large-cap alt | Three-bar declining volume | Directional size vetoed |
| Stablecoin | Consecutive 20 bp peg watches | Escalated note. Size stays zero |
| DeFi | Last bar range above 8% | Directional size vetoed |
| Meme | Last volume above 5x median | Paper size halved |
| L2 | Six-bar lag versus benchmark beyond 5% | Directional size vetoed |
| RWA | Ten-bar absolute drift above 6% | Slow-sleeve invalidation |
| Perpetual | Absolute funding at or above 30 bps | Extreme-funding halt |

## Cyber and data security

`crypto-intel cyber` prints three policy objects.

- Key scope allowlist: `market_read` and `public_ticker` only. Trade, withdraw, transfer, order, futures-write, and margin scopes are refused.
- Key ceremony checklist: two-person, offline, no seed in git, no automated key generation.
- Incident playbook: detect, contain with the kill switch, human secret rotation outside this repo, auditor clear. Automated remediation and live trading stay disabled.
- Research packet: SHA-256 of the catalog digest plus a `SYNTHETIC` or `PUBLIC_READ` label. Not an order signature.

Control ids added: `PR.AC-7`, `RS.RP-1`, `PR.IP-5`.
