# Version 0.21 calendar guards and data-residency plane

`crypto-intel v21` is a seventeenth pass. It can only shrink paper size. It does
not open a socket, store key material, or place an order. These overlays sit on
top of the class playbook in `docs/asset-class-strategies.md`. They do not
replace the entry rules and they cannot raise a class cap.

| Class | Guard | Effect |
|---|---|---|
| Major | Session gap | Open at least 1.5 percent from the prior close halves size |
| Large-cap alt | Beta shock | Two same-sign jumps, the last at least 6 percent, halves size |
| Stablecoin | Peg acceleration | Deviation up by at least 15 bp is a watch. Size stays zero |
| DeFi | Volume air-pocket | Price up 3 percent on volume below half the median halves size |
| Meme | Wick rejection | Upper wick more than twice the body zeroes size |
| L2 | Lead fade | A three-bar lead followed by a negative three-bar return halves size |
| RWA | Stale print | Three identical closes halves size |
| Perpetual | Basis stress | Funding sign against a 3 percent drift zeroes size |

`crypto-intel clock` publishes an offline research clock with a per-class
freshness window. `crypto-intel residency` describes the data-residency plane.
Allowed region labels are `SG`, `EU`, and `US-research`. Research series, audit
events, secrets, and personal data require encryption at rest and cannot leave
the origin region. Encryption, audit-sign, and break-glass keys are separated.
None of those keys can trade. Trade, withdrawal, seed, private-key, and api-key
scopes are refused. A region transfer cannot enable live trading.

This is a research control, not a MAS TRM, PDPA, SOC, NIST, or ISO certification.
