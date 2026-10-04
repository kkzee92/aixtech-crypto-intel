# Version 0.9 class guards, alerts, and zero-trust plane

v0.9 adds a fifth-pass research guard per asset class, an information alert
router, and a zero-trust description of the research plane. None of these paths
can place an order, raise a class size cap, store a secret, or enable live
trading.

## Class guards

`crypto-intel v09` applies a rule that can only shrink paper size.

| Class | v0.9 guard | Effect |
|---|---|---|
| Major | Drawdown-cluster haircut | Five consecutive lower closes halve size |
| Large-cap alt | Idiosyncratic gap veto | Open gap above 6% zeroes size |
| Stablecoin | Tertiary peg watch | Deviation of 10 bp or more is a watch. Size stays zero |
| DeFi | Bar-range stress halt | Last bar range above 5% zeroes size |
| Meme | Three-bar chase veto | A 25% rise over three rising bars zeroes size |
| L2 | Benchmark-lag haircut | Lagging the benchmark by more than 4% over six bars halves size |
| RWA | Stale-print veto | More than 36 hours between the last two prints zeroes size |
| Perpetual | Extreme-funding veto | Absolute funding above 20 bp zeroes size |

These are research filters on synthetic or injected public prints. They are not
forecasts and not a recommendation to trade.

## Alert router

`crypto-intel alerts` emits information severity only: `info`, `watch`, or
`research_halt`. A stablecoin deviation of 50 bp or more is a research halt for
the book. The payload sets `order_instruction` to false.

## Zero-trust research plane

`crypto-intel zerotust` reports the defensive architecture:

- zones are untrusted input, research, control, and audit; there is no execution zone
- control families follow identify, protect, detect, respond, recover, without claiming a certification
- secrets, wallet seeds, and personal data stay refused, with zero retention in this tree
- a parameter-digest change needs two distinct acknowledgements and still cannot enable live trading
- backups, if a later deployment adds them, cover synthetic fixtures and redacted audit only
- expected protection if a store ever leaves this repository is AES-256-GCM at rest and TLS in transit, with keys outside git

This is a research control description, not a certification and not legal advice.
The PDPA tripwire remains a tripwire, not a data-protection programme.
