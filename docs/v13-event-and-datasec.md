# Version 0.13 event guards and data-security plane

v0.13 adds a ninth-pass research guard per asset class, an offline information
radar, and a data-security plane for the automated information system. None of
these paths can place an order, raise a class size cap, store a secret, or
enable live trading.

This is research on synthetic or injected public prints. It is not a forecast,
not a recommendation to trade, and not a certification or legal advice.

## Class event guards

`crypto-intel v13` applies a rule that can only shrink paper size.

| Class | v0.13 guard | Effect |
|---|---|---|
| Major | Failed-auction haircut | Close in the bottom quarter of a bar whose range is at least 1.5 percent halves size |
| Large-cap alt | Failed-follow-through haircut | An up bar followed by a down close halves size |
| Stablecoin | Depeg-velocity watch | Deviation wider than the prior bar and at least 15 bp is a watch. Size stays zero |
| DeFi | Range-expansion haircut | Last bar range at least twice the prior median halves size |
| Meme | Exhaustion-wick veto | Upper wick at least 60 percent of the range and a close below the open zeroes size |
| L2 | Participation-fade haircut | A three percent six-bar move with last volume below 0.6 times the prior median halves size |
| RWA | Halted-print veto | Four bars with range under 5 bp of price zeroes size |
| Perpetual | Funding-acceleration haircut | Absolute funding rising across three bars and last absolute funding at least 4 bp halves size |

## Information radar

`crypto-intel radar` stamps a lineage digest over the fixture label and the
already-scored paper rows. The label must be synthetic. The radar note is a
review artifact. It is not an order instruction and cannot raise size.

## Data-security plane

`crypto-intel datasec` reports the information-system data plane:

- ingest, score, report, and archive zones cannot trade
- ingest is default-deny and has no order host
- purpose is bound to research information
- secrets and personal data are refused, so they are not backed up
- archive keeps lineage digests only
- no role has standing privilege to trade or enable live trading
- the map is a research control design, not a certification
