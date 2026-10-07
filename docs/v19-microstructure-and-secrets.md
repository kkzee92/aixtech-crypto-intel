# Version 0.19 microstructure guards and secrets lifecycle

`crypto-intel v19` is a fifteenth pass. It can only shrink paper size. It does
not open a socket, store key material, or place an order.

| Class | Guard | Effect |
|---|---|---|
| Major | Gap-and-fail haircut | A gap above 1.5 percent that closes back through the open halves size |
| Large-cap alt | Upper-wick haircut | An upper wick above half the bar halves size |
| Stablecoin | Peg-velocity watch | Four-bar absolute deviation above 30 bp is a watch. Size stays zero |
| DeFi | Volume-price divergence | A rising price with three falling volumes halves size |
| Meme | Upper-wick veto | An upper wick above 55 percent of the range zeroes size |
| L2 | Range-dispersion haircut | A last range above twice the median range halves size |
| RWA | Session-gap haircut | An open gap above 2 percent versus the prior close halves size |
| Perpetual | Funding-price disagreement | Negative funding with a 3 percent six-bar rise halves size |

`crypto-intel tape` publishes an offline digest. `crypto-intel secrets`
describes the secrets-lifecycle plane. Discussable scopes are `market_read`
(90 days), `audit_sign` (180 days), and `break_glass` (30 days). Trade,
withdrawal, seed, and private-key names are refused. A researcher and an
auditor must both acknowledge a rotation. Acknowledgement cannot enable live
trading. No key bytes are generated or stored.

This is a research design, not a certification and not financial advice.
