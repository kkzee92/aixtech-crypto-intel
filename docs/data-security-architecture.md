# Data security architecture

Version 0.4. Research design, not a certified control set and not legal advice.
Cyber controls here are defensive: classification, retention, rotation policy,
integrity, and refusal of trade credentials. This repository does not generate
keys, does not store secrets, and does not describe how to attack an exchange
or a wallet.

## Data classes

| Class | Examples | Retention | Handling |
|---|---|---|---|
| Public market | symbol, OHLCV, funding | 400 days in a future store | Synthetic in this repo |
| Research audit | hash-chain events | 365 days | Redact before write |
| Synthetic fixture | labelled candles | long research life | Must stay labelled SYNTHETIC |
| Secret | read-only market key | not stored here | Name must say read, market, or public. Rotate at 90 days outside this repo |
| Prohibited | trade key, withdrawal key, wallet, NRIC, email, phone | 0 | Refused by policy and PDPA tripwire |

## Trust boundaries

1. Fixture or injected public ticker, attested by label plus body hash.
2. Quality gate, then class strategy, then confirmation, then risk gate.
3. Paper fill only. No order router.
4. Audit chain. Operator kill switch. Auditor must confirm a clear.
5. Trade and withdrawal credentials never cross the boundary.

## Key ceremony

No ceremony runs in this repository. If a later system needs a read-only market
credential, the intended control is: generate it in the exchange UI, store it
in a secret manager, never in git, rotate it every 90 days, and keep it in a
different account from any trade credential. This codebase still refuses trade
credential names.

## Integrity and detection

- Catalog digest covers class parameters and v0.4 overlays.
- Audit events are SHA-256 chained after redaction.
- Feed status flags non-positive, stale, and 25% jump prints.
- Quality gate flags 40% close jumps, duplicate timestamps, and zero volume.
- Clock skew above 120 seconds is not accepted.

## What this is not

- Not a penetration-test kit.
- Not a live trading or withdrawal client.
- Not a substitute for exchange security, custody, or a human compliance review.
