# Version 0.12 basis guards and custody plane

v0.12 adds an eighth-pass research guard per asset class, an offline information
desk, and a custody data-security plane. None of these paths can place an
order, raise a class size cap, store a secret, or enable live trading.

This is research on synthetic or injected public prints. It is not a forecast,
not a recommendation to trade, and not a certification or legal advice.

## Class basis and inventory guards

`crypto-intel v12` applies a rule that can only shrink paper size.

| Class | v0.12 guard | Effect |
|---|---|---|
| Major | Basis-instability haircut | Funding sign flip across the last three bars halves size |
| Large-cap alt | Thin-participation haircut | Last volume below half the prior median halves size |
| Stablecoin | Persistent-depeg watch | Three closes more than 20 bp from peg is a watch. Size stays zero |
| DeFi | Inventory-unwind veto | Four rising closes and a move above 10 percent zeroes size |
| Meme | Wash-print veto | Volume above 8x the median with a bar move under 1 percent zeroes size |
| L2 | Imbalance haircut | Bar range above 5 percent and volume below the median halves size |
| RWA | Unusual-print veto | Volume above 3x the median zeroes size |
| Perpetual | Crowded-basis haircut | Funding and three-bar drift sharing a sign, with funding above 5 bp, halves size |

## Information desk

`crypto-intel desk` stamps a lineage digest over the fixture label and the
already-scored paper rows. The label must be synthetic. The desk note is a
review artifact. It is not an order instruction and cannot raise size.

## Custody and data-security plane

`crypto-intel custody` reports a research custody plane:

- hot, warm, and cold zones hold notes, synthetic fixtures, and digests only
- the withdrawal allowlist in this tree is empty and immutable
- an operator cannot sign a research digest
- two acknowledgements of a digest still cannot enable live trading
- seed, private-key, trade-secret, withdrawal-key, and personal-data classes are refused
- domains follow a MAS TRM-style map and are not a certification
- there is no execution zone

The PDPA tripwire remains a tripwire, not a data-protection programme.
