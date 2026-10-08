# v0.22 depth guards and provenance plane

Eighteenth pass. Research only. Not a certified control and not an order router.

## Depth guards

`apply_v22` can only shrink a proposed paper size. Stablecoin size stays zero.

| Class | Guard | Effect |
|---|---|---|
| Major | Stop-run haircut | Last range at least 2.5x the prior median halves size |
| Large-cap alt | Failed-auction haircut | A high that breaks the prior five-bar high and closes back inside halves size |
| Stablecoin | Peg-persistence watch | Two closes at least 20 bp off peg. Size stays zero |
| DeFi | Liquidity-vacuum haircut | Volume halves while the range expands: size halves |
| Meme | Wash-print veto | A 4x volume spike that closes near the open zeroes size |
| L2 | Lead-reversal haircut | A 2% three-bar lead followed by a fade halves size |
| RWA | Thin-gap haircut | A 2% open gap on below-median volume halves size |
| Perpetual | Funding-flip veto | A funding-sign change zeroes size |

## Provenance plane

`crypto-intel provenance` describes the chain-of-custody plane. `crypto-intel chain`
hashes depth-guard notes into an offline digest. Neither path stores key material
or opens an execution zone.

Allowed labels are `SYNTHETIC` and `PUBLIC_READ`. Collector, reviewer, and auditor
duties can attest and cannot trade. Trade, withdrawal, seed, private-key, and
api-key scopes are refused. Secret and personal classes cannot enter a published
handoff.
