# Version 0.8 information desk, zones, and class overlays

v0.8 adds an offline information desk, data-security zones, and a fourth-pass
overlay per asset class. None of these paths can place an order or raise a
class size cap.

## Information desk

`crypto-intel desk` builds a research dossier from a labelled fixture:

1. freshness is checked against the v0.7 class SLA
2. a correlation shock counts non-stable series down 4 percent over three bars
3. three or more stressed series scale the paper book to 0.5
4. a stale series or a failed zone check scales the paper book to 0

The package does not poll an exchange. An external scheduler may invoke the CLI.

## Class overlays

`crypto-intel overlay` applies a rule that can only shrink paper size.

| Class | v0.8 overlay | Effect |
|---|---|---|
| Major | Weak-close haircut | Close in the bottom quarter of the bar halves size |
| Large-cap alt | Upper-wick veto | Wick above 60 percent of the range zeroes size |
| Stablecoin | Peg-persistence watch | Three closes outside 20 bps is a watch. Size stays zero |
| DeFi | Liquidity-drain haircut | Volume below 40 percent of the recent mean halves size |
| Meme | Wick-rejection veto | Upper wick above half the range zeroes size |
| L2 | Benchmark-divergence veto | Six-bar excess return below -5 percent zeroes size |
| RWA | Intrabar divergence haircut | Open-to-close above 3 percent halves size |
| Perpetual | Crowded-funding veto | Absolute funding at or above 15 bps zeroes size |

## Cyber and data security

`crypto-intel zones` reports four zones:

- public-market: symbol, OHLCV, funding
- research-derived: signal, paper size, audit digest, dossier
- restricted-ops: kill switch and source attestation
- forbidden: exchange keys, withdrawal destinations, private keys, emails, wallet addresses

Researcher cannot read restricted-ops. No role can read the forbidden zone.
A seal is a SHA-256 integrity check and does not authorize live trading.

This is a research control description, not a certification and not legal advice.
