# Version 0.12 microstructure guards and data lineage

v0.12 adds an eighth-pass research guard per asset class, an offline strategy
card, and a data-lineage zone map. None of these paths can place an order,
raise a class size cap, store a secret, or enable live trading.

This is research on synthetic or injected public prints. It is not a forecast,
not a recommendation to trade, and not a certification or legal advice.

## Class microstructure guards

`crypto-intel v12` applies a rule that can only shrink paper size.

| Class | v0.12 guard | Effect |
|---|---|---|
| Major | Participation haircut | Last volume below 40% of the 8-bar median halves size |
| Large-cap alt | Wick-rejection veto | Upper wick at least 60% of the bar and a down close zeroes size |
| Stablecoin | Secondary peg watch | Close 15 bp or more from 1.0 is a watch. Size stays zero |
| DeFi | Impact haircut | Range above 4% and volume above 1.8x the median halves size |
| Meme | Climax veto | Last bar range above 12% of the close zeroes size |
| L2 | Benchmark-lag haircut | Six-bar return more than 4% behind the benchmark halves size |
| RWA | Thin-print haircut | Last volume below half the median halves size |
| Perpetual | Basis-blowout veto | Bar range above 5% and absolute funding above 10 bp zeroes size |

## Strategy card

`crypto-intel cards` summarises already-scored paper rows by symbol and stamps
a digest. The card is a review artifact. It is not an order instruction and
cannot raise size.

## Cyber and data-security lineage

`crypto-intel lineage` reports four zones and a retention matrix:

- ingest accepts only a synthetic fixture or an attested public print
- research holds classified features and paper signals, never an order
- audit holds the hash chain and a redacted digest
- secrets is a refused zone: credentials, seeds, and personal data are not stored

Transport policy, if a future public feed is added, is TLS 1.2 or newer in
transit and AES-256 at rest. This tree does not call a network feed and does
not keep keys in git. The PDPA tripwire remains a tripwire, not a
data-protection programme.
