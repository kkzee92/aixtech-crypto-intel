# Version 0.10 class guards and cyber architecture

Research description only. Not a certification, not legal advice, and not a
live trading system. `crypto-intel v10` is a sixth pass after the class rule.
It can only shrink paper size.

| Class | Guard | Effect |
|---|---|---|
| Major | Session-liquidity haircut | Volume under half the 8-bar median halves size |
| Large-cap alt | Wash-print veto | Volume above 2x with a bar range under 0.4% zeroes size |
| Stablecoin | Peg-persistence watch | Three closes at least 15 bp off peg is a watch. Size stays zero |
| DeFi | Liquidity-cliff haircut | Volume under 40% of the prior bar halves size |
| Meme | Wick-rejection veto | Close in the bottom 40% of the bar zeroes size |
| L2 | Fee-spike proxy | Bar range above 3.5% halves size. Missing benchmark zeroes size |
| RWA | NAV-gap halt | Open gap above 3% versus the prior close zeroes size |
| Perpetual | Basis-blowout veto | Six-bar absolute drift above 6% zeroes size |

## Cyber and data-security architecture

`crypto-intel cyberarch` publishes the snapshot:

- Zones: untrusted input, research, control, audit, evidence. No execution zone.
- Each asset class has a field list, an integrity check, and a retention rule.
- Egress stays default-deny. Tests inject fetchers. The default path does not open a socket.
- Trade, withdraw, and transfer credential names remain refused.
- The policy text is hashed into an evidence digest so a silent edit is detectable.
- The report cannot enable live trading and has no order path.

This does not replace access control, vendor review, or a human decision before
any future system outside this repository.
