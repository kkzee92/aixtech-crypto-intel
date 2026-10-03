# Version 0.7 automation, sleeves, and cyber architecture

v0.7 adds an offline information pipeline, a third-pass sleeve per asset class,
and a supply-chain / data-flow snapshot. None of these paths can place an order
or raise a class size cap.

## Information pipeline

`crypto-intel pipeline` prints the declared stages:

1. ingest
2. attest
3. quality
4. class strategy
5. risk gate
6. cross overlay
7. class enhance
8. sleeve
9. brief
10. audit

Freshness budgets are information SLAs, not execution deadlines. A stale series
scales the paper book to zero. The package does not poll an exchange.

| Class | Freshness SLA |
|---|---|
| Major | 60s |
| Large-cap alt | 120s |
| Stablecoin | 30s |
| DeFi | 180s |
| Meme | 60s |
| L2 | 120s |
| RWA | 900s |
| Perpetual | 30s |

## Class sleeves

`crypto-intel sleeve` applies a rule that can only shrink paper size.

| Class | v0.7 sleeve | Effect |
|---|---|---|
| Major | ATR expansion haircut | Last bar range above 2x the prior median halves size |
| Large-cap alt | Relative-lag veto | Missing benchmark, or lagging it by more than 2%, zeroes size |
| Stablecoin | Peg-dispersion watch | Bar range of 40 bps or more is a watch. Size stays zero |
| DeFi | Protocol-gap halt | Open gap above 5% zeroes size |
| Meme | Volume-decay haircut | Volume below half the recent peak halves size |
| L2 | Sequencer-gap proxy | Open gap above 4% zeroes size |
| RWA | Stale-print haircut | Three identical closes halve size |
| Perpetual | Funding-sign flip | A sign change versus the prior bar zeroes carry or fade size |

## Cyber and data security

`crypto-intel supply` reports:

- runtime third-party imports are empty; network imports are not used
- data-flow classes are research or restricted operations, and personal data is refused
- researcher, reviewer, auditor, and operator roles cannot place an order
- break-glass containment cannot set live trading on
- fixture integrity requires the `SYNTHETIC` label and hashes the body

This is a research control description, not a certification and not legal advice.
