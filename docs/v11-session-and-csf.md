# Version 0.11 session guards and CSF control plane

v0.11 adds a seventh-pass research guard per asset class, an offline information
bulletin, and a NIST CSF 2.0-style control map. None of these paths can place an
order, raise a class size cap, store a secret, or enable live trading.

This is research on synthetic or injected public prints. It is not a forecast,
not a recommendation to trade, and not a certification or legal advice.

## Class session guards

`crypto-intel v11` applies a rule that can only shrink paper size.

| Class | v0.11 guard | Effect |
|---|---|---|
| Major | Extension haircut | Close more than 8% above the 8-bar mean halves size |
| Large-cap alt | Gap haircut | Open gap above 6% versus the prior close halves size |
| Stablecoin | Intrabar dispersion watch | High-low range of 30 bp or more is a watch. Size stays zero |
| DeFi | Range-expansion veto | Last bar range above twice the prior median zeroes size |
| Meme | Consecutive-gap veto | Two opens gapping up more than 8% zeroes size |
| L2 | Stuck-print veto | Three identical volumes zeroes size |
| RWA | Session-gap veto | Open gap above 4% versus the prior close zeroes size |
| Perpetual | Crowded-funding veto | Absolute funding above 15 bp and volume above 2x the median zeroes size |

## Information bulletin

`crypto-intel bulletin` summarises already-scored paper rows by asset class and
stamps a digest. The bulletin is a review artifact. It is not an order
instruction and cannot raise size.

## Cyber and data-security map

`crypto-intel csf` reports a defensive control map aligned to Govern, Identify,
Protect, Detect, Respond, and Recover:

- researcher, auditor, and operator roles cannot trade or enable live trading
- credential, seed, withdrawal-key, and personal-data classes are refused
- integrity is the existing hash-chained audit
- residency for this tree is synthetic fixtures only
- there is no execution zone

The PDPA tripwire remains a tripwire, not a data-protection programme.
