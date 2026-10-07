# Version 0.13 fragmentation guards and cyber resilience

v0.13 adds a ninth-pass research guard per asset class, an offline information
mesh, and a cyber-resilience plane. None of these paths can place an order,
raise a class size cap, store a secret, or enable live trading.

This is research on synthetic or injected public prints. It is not a forecast,
not a recommendation to trade, and not a certification or legal advice.

## Class venue-fragmentation guards

`crypto-intel v13` applies a rule that can only shrink paper size.

| Class | v0.13 guard | Effect |
|---|---|---|
| Major | Venue-disagreement haircut | Last bar range above 2.5x the prior median range halves size |
| Large-cap alt | Listing-fragmentation haircut | A gap above 4 percent on below-median volume halves size |
| Stablecoin | Redemption-stress watch | Peg oscillation beyond 15 bp is a watch. Size stays zero |
| DeFi | Oracle-gap veto | A jump above 6 percent without participation zeroes size |
| Meme | Exhaustion veto | A burst above 8 percent followed by three declining closes zeroes size |
| L2 | Sequencer-stall haircut | Busy volume with a frozen print halves size |
| RWA | Stale-attestation veto | Three unchanged closes zeroes size |
| Perpetual | Funding-price disagreement haircut | Opposed funding and last-bar return, both material, halves size |

## Information mesh

`crypto-intel mesh` compares an injected primary close with an injected
secondary close. No socket is opened. A disagreement above the class threshold
halves that row's paper size and marks it contested. Agreement leaves size
unchanged. The mesh cannot raise size and carries no order instruction.

| Class | Disagreement threshold |
|---|---|
| Major | 6% |
| Large-cap alt | 8% |
| Stablecoin | 0.3% |
| DeFi | 7% |
| Meme | 12% |
| L2 | 7% |
| RWA | 4% |
| Perpetual | 6% |

## Cyber-resilience plane

`crypto-intel resilience` reports a research resilience plane:

- identify, protect, detect, respond, and recover controls are research-only
- trade and withdrawal key scopes are refused and are not stored in this tree
- data residency is the research repository; production custody and personal-data regions are refused
- backup holds digests and redacted audit notes only; there is no seed backup
- backup restore cannot enable live trading
- an operator cannot read the mesh
- two acknowledgements still cannot enable live trading
- there is no execution zone

The map is an ICT-style research checklist. It is not a DORA, MAS TRM, or NIST certification. The PDPA tripwire remains a tripwire, not a data-protection programme.
