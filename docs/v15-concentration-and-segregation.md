# Version 0.15 concentration guards, ledger, and segregation plane

v0.15 adds an eleventh-pass research guard per asset class, an offline information
ledger, and a segregation plane for cyber and data security. None of these
paths can place an order, raise a class size cap, store a secret, or enable
live trading.

This is research on synthetic or injected public prints. It is not a forecast,
not a recommendation to trade, and not a certification or legal advice.

## Class concentration guards

`crypto-intel v15` applies a rule that can only shrink paper size.

| Class | v0.15 guard | Effect |
|---|---|---|
| Major | Open-gap haircut | A gap beyond 1.5 percent that closes further from the prior close halves size |
| Large-cap alt | Failed-expansion haircut | Three widening ranges whose close returns inside the prior bar halves size |
| Stablecoin | Premium-persistence watch | A close beyond 50 bp is a watch. Size stays zero |
| DeFi | Unlock-window veto | Three falling closes and three expanding ranges zero size |
| Meme | Climax veto | Volume above 4x the prior median and a close in the lower 40 percent of the bar zeroes size |
| L2 | Sequencer-stall haircut | Three unchanged closes and declining volume halves size |
| RWA | Oracle-gap veto | An open more than 1.5 percent from the prior close zeroes size |
| Perpetual | Crowded-expansion haircut | Three widening ranges and funding that agrees with the paper side halves size |

## Information ledger

`crypto-intel ledger` appends an offline automation packet from the v0.15
rows. Stages are ingest, classify, concentration-guard, attest, and append-ledger.
No socket is opened. The packet cannot raise size and carries no order
instruction. The digest chains to the previous digest. An automation runner cannot enable live trading.

## Segregation plane

`crypto-intel segregation` reports a research segregation plane:

- zones are research, audit, and automation; there is no execution zone
- a researcher cannot append the audit log or clear a halt
- an automation runner cannot read research records or write the audit log
- an auditor cannot place an order
- dual control of a research digest cannot enable live trading
- allowed data is synthetic research, attested public prints, and redacted audit notes
- seeds, private keys, trade secrets, withdrawal keys, personal data, and customer wallets are refused
- credential and personal-data retention stay at zero
- encryption is an operator expectation; keys are not stored in this tree

The map is a research checklist. It is not a MAS TRM, PDPA, SOC 2, NIST, or ISO certification. The PDPA tripwire remains a tripwire, not a data-protection programme.
