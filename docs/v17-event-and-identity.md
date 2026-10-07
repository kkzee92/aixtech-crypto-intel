# Version 0.17 event-window guards, beacon, and identity plane

v0.17 adds a thirteenth-pass research guard per asset class, an offline
information beacon, and an identity-bound research plane. None of these paths
can place an order, raise a class size cap, store a secret, or enable live
trading.

This is research on synthetic or injected public prints. It is not a forecast,
not a recommendation to trade, and not a certification or legal advice.

## Class event-window guards

`crypto-intel v17` applies a rule that can only shrink paper size.

| Class | v0.17 guard | Effect |
|---|---|---|
| Major | Range-expansion haircut | Last true range above 2.5x the prior median halves size |
| Large-cap alt | Reversal-window haircut | A material three-bar path flipped by a material last bar halves size |
| Stablecoin | Wick-straddle watch | A bar that crosses both sides of a 15 bp peg band is a watch. Size stays zero |
| DeFi | Thin-tape veto | Volume below 40 percent of median with a 2 percent move zeroes size |
| Meme | Exhaustion haircut | Three expanding ranges and a falling close halves size |
| L2 | Reopen-gap haircut | An open gap beyond 1.2 percent on below-median volume halves size |
| RWA | Auction-window veto | Two consecutive gaps, each beyond 0.6 percent, zeroes size |
| Perpetual | Inventory-skew haircut | Extreme funding with a last range beyond 1.5 percent of price halves size |

## Information beacon

`crypto-intel beacon` builds an offline packet from the v0.17 rows. Stages are
ingest, classify, event-guard, and beacon. No socket is opened. The packet
cannot raise size and carries no order instruction. The digest is stable for
the same rows. An automation runner cannot enable live trading.

## Identity plane

`crypto-intel identity` reports a research identity plane:

- zones are research, audit, and identity; there is no execution zone
- a session is bound to one role and cannot be reused across roles
- trade, withdrawal, seed, private-key, and live scopes are refused
- standing credentials are refused
- a researcher or auditor may emit a beacon on a research-read scope
- an operator cannot emit a beacon or trade
- an automation runner cannot mint a session
- dual acknowledgement of a session digest cannot enable live trading
- credential and personal-data retention stay at zero

The map is a research checklist. It is not a MAS TRM, PDPA, SOC 2, NIST, or ISO
certification. The PDPA tripwire remains a tripwire, not a data-protection
programme.
