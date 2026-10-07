# Version 0.16 correlation-break guards, radar, and DLP plane

v0.16 adds a twelfth-pass research guard per asset class, an offline information
radar, and a data-loss-prevention egress plane. None of these paths can place
an order, raise a class size cap, store a secret, or enable live trading.

This is research on synthetic or injected public prints. It is not a forecast,
not a recommendation to trade, and not a certification or legal advice.

## Class correlation guards

`crypto-intel v16` applies a rule that can only shrink paper size.

| Class | v0.16 guard | Effect |
|---|---|---|
| Major | Whipsaw haircut | Four alternating returns, each beyond 0.5 percent, halves size |
| Large-cap alt | Volume-divergence haircut | A 1 percent rise with three falling volumes halves size |
| Stablecoin | Peg-persistence watch | Four closes on one side of par, any beyond 20 bp, is a watch. Size stays zero |
| DeFi | Cascade veto | Four same-sign returns whose mean absolute move exceeds 4 percent zeroes size |
| Meme | Participation-break haircut | Three rising closes on falling volume halves size |
| L2 | Path-break haircut | Six-bar and three-bar returns that disagree, both beyond 2 percent, halves size |
| RWA | Jump-cluster veto | Three same-sign gaps, each beyond 0.4 percent, zeroes size |
| Perpetual | Funding-divergence haircut | Funding and six-bar drift that disagree, both material, halves size |

## Information radar

`crypto-intel radar` builds an offline packet from the v0.16 rows. Stages are
ingest, classify, correlation-guard, and radar. No socket is opened. The packet
cannot raise size and carries no order instruction. The digest is stable for
the same rows. An automation runner cannot enable live trading.

## DLP egress plane

`crypto-intel dlp` reports a research data-loss-prevention plane:

- zones are research, audit, and dlp; there is no execution zone
- the only allowed destination is a local research digest
- exchange order, withdrawal, public issue, chat paste, and email destinations are refused
- secret, wallet, email, and Singapore-style phone strings are blocked before egress
- an automation runner cannot emit a digest
- no DLP exception can open an order or withdrawal path
- credential and personal-data retention stay at zero

The map is a research checklist. It is not a MAS TRM, PDPA, SOC 2, NIST, or ISO
certification. The PDPA tripwire remains a tripwire, not a data-protection
programme.
