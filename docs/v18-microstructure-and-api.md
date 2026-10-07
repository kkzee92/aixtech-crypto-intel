# Version 0.18 microstructure guards, information wire, and API plane

v0.18 adds a fourteenth-pass research guard per asset class, an offline
information wire, and an API data-security plane. None of these paths can
place an order, raise a class size cap, store a secret, or enable live trading.

This is research on synthetic or injected public prints. It is not a forecast,
not a recommendation to trade, and not a certification or legal advice.

## Class microstructure guards

`crypto-intel v18` applies a rule that can only shrink paper size.

| Class | v0.18 guard | Effect |
|---|---|---|
| Major | Spread-proxy haircut | Last bar range above 1.5% on below-median volume halves size |
| Large-cap alt | Failed-hold veto | Prior bar cleared the five-bar high and the last close fell back through it: size zero |
| Stablecoin | Widening-peg watch | Three strictly increasing deviations, last at least 20 bps, is a watch. Size stays zero |
| DeFi | Dislocation veto | Open-to-close move above 4% zeroes size |
| Meme | Blow-off veto | Volume above 4x median and a down close zeroes size |
| L2 | Sequencer-gap haircut | Open gap above 2% versus the prior close halves size |
| RWA | Too-fast veto | Four-bar move above 3% zeroes size |
| Perpetual | Funding-acceleration haircut | Funding move above 8 bps versus three bars ago halves size |

## Information wire

`crypto-intel wire` builds an offline packet from the v0.18 rows. Stages are
ingest, classify, microstructure-guard, and wire. No socket is opened. The
packet cannot raise size and carries no order instruction. The digest is stable
for the same rows.

## API plane

`crypto-intel apiscope` reports a research API and data-security plane:

- zones are research, market-data, and audit; there is no execution zone
- discussable scopes are market-read and public ticker only
- trade, withdrawal, transfer, seed, private-key, and live scopes are refused
- the withdrawal allowlist is empty
- a read key cannot sign
- order intent is not stored
- an automation runner cannot call an exchange
- DeFi and RWA dislocation notes are research flags, not oracle attestations

The map is a research checklist. It is not a MAS TRM, PDPA, SOC 2, NIST, or ISO
certification. The PDPA tripwire remains a tripwire, not a data-protection
programme.
