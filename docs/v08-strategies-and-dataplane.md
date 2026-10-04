# Version 0.8 class overlays, schedule, and data plane

v0.8 adds a fourth-pass research overlay per asset class, a declared offline
information cadence, and a data-plane architecture. None of these paths can
place an order, raise a class size cap, or store a secret.

## Class overlays

`crypto-intel v08` applies a rule that can only shrink paper size.

| Class | v0.8 overlay | Effect |
|---|---|---|
| Major | Thin-liquidity haircut | Last volume below half the prior median halves size |
| Large-cap alt | Close-location haircut | Close in the bottom quarter of the bar halves size |
| Stablecoin | Secondary peg watch | Deviation of 20 bp or more is a watch. Size stays zero |
| DeFi | Volume-collapse halt | Last volume below 30% of the prior median zeroes size |
| Meme | Upper-wick veto | Upper wick above 60% of the bar range zeroes size |
| L2 | Fee-spike proxy | Last range above 3x the prior median halves size |
| RWA | Slow-confirmation veto | A long that is not above the close three bars ago is zeroed |
| Perpetual | Activity-spike haircut | Volume above 3x the prior median halves size |

These are research filters on synthetic or injected public prints. They are not
forecasts and not a recommendation to trade.

## Information schedule

`crypto-intel schedule` prints a cadence an external scheduler may use to call
the CLI. The package does not open a socket.

| Class | Cadence |
|---|---|
| Major | 15 min |
| Large-cap alt | 30 min |
| Stablecoin | 5 min |
| DeFi | 30 min |
| Meme | 15 min |
| L2 | 30 min |
| RWA | 240 min |
| Perpetual | 5 min |

## Data plane

`crypto-intel dataplane` reports the defensive architecture:

- zones are research, control, and audit; there is no execution zone
- allowed classes are public market, research audit, synthetic fixture, and restricted operations
- trade credentials, withdrawal credentials, wallet seeds, and personal data are refused
- expected protection if a store ever leaves this repository is AES-256-GCM at rest and TLS in transit, with keys outside git
- dual control is required before a paper size cap can change
- exports are hash envelopes over a research label, not signatures over orders

This is a research control description, not a certification and not legal advice.
