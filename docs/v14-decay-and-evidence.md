# Version 0.14 decay guards, watchtower, and evidence plane

v0.14 adds a tenth-pass research guard per asset class, an offline information
watchtower, and an evidence plane for cyber and data security. None of these
paths can place an order, raise a class size cap, store a secret, or enable
live trading.

This is research on synthetic or injected public prints. It is not a forecast,
not a recommendation to trade, and not a certification or legal advice.

## Class decay guards

`crypto-intel v14` applies a rule that can only shrink paper size.

| Class | v0.14 guard | Effect |
|---|---|---|
| Major | Participation-decay haircut | Three falling volumes with a last return beyond 1 percent halves size |
| Large-cap alt | Failed-follow-through haircut | A prior move beyond 3 percent that is retraced by more than half halves size |
| Stablecoin | Depeg-persistence watch | Three closes beyond 20 bp on one side are a watch. Size stays zero |
| DeFi | Liquidity-vacuum veto | Volume below 40 percent of the prior median and a range above 2x the median zeroes size |
| Meme | Wick-rejection veto | After an up bar, an upper wick more than twice the body and a down close zeroes size |
| L2 | Bridge-flow haircut | Volume above 3x the prior median with a range under 0.3 percent halves size |
| RWA | Attestation-gap veto | A flat print on volume below 10 percent of the prior median zeroes size |
| Perpetual | Funding-persistence haircut | Three crowded funding prints and a last return beyond 1.5 percent in the same direction halves size |

## Information watchtower

`crypto-intel watchtower` builds an offline automation packet from the v0.14
rows. Stages are ingest, classify, decay-guard, attest, and publish-digest.
No socket is opened. The packet cannot raise size and carries no order
instruction. An automation runner cannot enable live trading.

## Evidence plane

`crypto-intel evidence` reports a research evidence plane:

- zones are research, audit, and automation; there is no execution zone
- detection cases cover secret-like strings, size-increase attempts, live-mode requests, feed jumps, and withdrawal paths
- every detection action is forbidden from enabling live trading
- evidence holds digests and redacted audit notes only; there is no seed backup
- evidence restore cannot enable live trading
- the automation runner cannot read evidence
- credential and personal-data retention stay at zero
- encryption is an operator expectation; keys are not stored in this tree

The map is a research checklist. It is not a SOC 2, NIST, MAS TRM, or ISO certification. The PDPA tripwire remains a tripwire, not a data-protection programme.
