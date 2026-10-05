# Version 0.10 liquidity guards and cyber data plane

v0.10 adds a sixth-pass research guard per asset class, a paper information pack,
and a defensive cyber / data-security plane. None of these paths can place an
order, raise a class size cap, store a secret, or enable live trading.

This is research on synthetic or injected public prints. It is not a forecast,
not a recommendation to trade, and not a certification or legal advice.

## Class liquidity guards

`crypto-intel v10` applies a rule that can only shrink paper size.

| Class | v0.10 guard | Effect |
|---|---|---|
| Major | Thin-book haircut | Last volume below half the 8-bar median halves size |
| Large-cap alt | Participation haircut | Last volume above 3x the 8-bar median halves size |
| Stablecoin | Peg-consensus watch | Deviation of 15 bp or more is a watch. Size stays zero |
| DeFi | Wick-rejection veto | A wick above 60% of the bar range zeroes size |
| Meme | Volume-collapse veto | Last volume below 20% of the prior bar zeroes size |
| L2 | Own-median volume haircut | Last volume below 40% of the 8-bar median halves size |
| RWA | Print-count veto | Fewer than 10 bars in the window zeroes size |
| Perpetual | Funding-sign-flip veto | A sign change across the last three funding prints zeroes size |

## Information pack

`crypto-intel pack` applies a 0.75 breadth haircut when four or more series
already have a positive paper size. The pack digest is a review token. It is
not an order instruction.

## Cyber and data-security plane

`crypto-intel cyberplane` reports the defensive architecture:

- zones are untrusted ingest, quality, research, control, audit, and a secrets boundary
- there is no execution zone
- data classes are public market, synthetic research, redacted audit, credential, and personal data
- credential and personal-data classes have zero retention and are refused in this tree
- key separation is market-read, audit-sign, and break-glass; none can trade or enable live trading
- expected protection if a store ever leaves this repository is AES-256-GCM at rest and TLS 1.2+ in transit, with keys outside git
- backups, if a later deployment adds them, cover synthetic fixtures and redacted audit only

The PDPA tripwire remains a tripwire, not a data-protection programme.
