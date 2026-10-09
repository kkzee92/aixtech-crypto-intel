# Version 0.23 flow guards and data-flow plane

`crypto-intel v23` is a nineteenth pass. It can only shrink paper size. It does
not open a socket, store key material, or place an order. These overlays sit on
top of the class playbook in `docs/asset-class-strategies.md`. They do not
replace the entry rules and they cannot raise a class cap.

| Class | Guard | Effect |
|---|---|---|
| Major | Vol spike | Last range at least twice the prior median range halves size |
| Large-cap alt | Failed follow-through | Close below the prior close with a range above 2 percent halves size |
| Stablecoin | Peg velocity | Absolute deviation up by at least 15 bp is a watch. Size stays zero |
| DeFi | Oracle-gap proxy | An open gap of at least 2.5 percent halves size |
| Meme | Exhaustion wick | An upper wick of at least 55 percent of the range zeroes size |
| L2 | Fee-spike proxy | Volume at least twice the median and a range above 3 percent halves size |
| RWA | Stale NAV | Three identical closes halves size |
| Perpetual | Carry squeeze | Negative funding and a three-bar rise above 3 percent zeroes size |

`crypto-intel bus` publishes an offline information bus with a provenance digest.
`crypto-intel flow` describes the research data-flow plane. Zones are ingest,
research, audit, and egress. Secret, personal, wallet, and trade-key classes
cannot reach egress. Audit records stay in the audit zone. Execution is not a
zone.

This is a research control, not a NIST, ISO, SOC, or PDPA certification.
