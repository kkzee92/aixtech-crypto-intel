# Version 0.7 liquidity gates and data residency

Paper research only. These rules cannot raise a class cap, provision a cloud
region, create a key, open a socket, or place an order.

## Per-class liquidity gate

`crypto-intel liquidity` runs after the v0.6 class enhancement. A wide bar
range is a slippage proxy, not an exchange quote.

| Class | Gate | Effect |
|---|---|---|
| Major | Last volume below 0.5x the prior median | Paper size halved |
| Large-cap alt | Bar range above 3% | Directional size vetoed |
| Stablecoin | Any proposed size | Size stays zero |
| DeFi | Bar range above 5% | Slippage-proxy veto |
| Meme | Last volume below 1,000 | Thin-print veto |
| L2 | Last volume below 0.6x the prior median | Paper size halved |
| RWA | Last volume below 0.5x the prior median | Off-session proxy haircut |
| Perpetual | Absolute funding at or above 10 bps and volume above 2x median | Crowded-tape haircut |

## Data residency and encryption

`crypto-intel residency` prints the policy. It does not contact a region.

- Labels: `SYNTHETIC` and `PUBLIC_READ` only. Personal, customer, secret, and production payloads are refused.
- Regions: `ap-southeast-1`, `eu-central-1`, and `research-local`. Unknown regions are refused.
- Encryption if a store is added later: AES-256-GCM at rest, TLS 1.2 or newer in transit. Keys and seeds stay outside the repo.
- Retention: synthetic fixtures 365 days, public reads 30 days, secrets and personal data zero.
- Vendor checklist: DPA required, no training on customer data, no withdrawal scope, residency declared. Not a signed contract.

Control ids added: `PR.DS-8`, `DE.CM-7`.
