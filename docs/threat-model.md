# Threat model

Version 0.5 maps the paper information system to STRIDE. The map is a reviewer
aid. It is not a penetration test, not an exploit guide, and not a certification.

| STRIDE | Research scenario | Control |
|---|---|---|
| Spoofing | Unlabelled data is treated as a market | Source attestation, data-class refusal |
| Tampering | Parameters or a single-symbol signal drift from the book context | Catalog digest, cross-asset overlay |
| Repudiation | A paper decision has no trail | Hash-chained audit log |
| Information disclosure | Secret-like or personal data reaches a fixture or log | Redaction, zero retention, label refusal |
| Denial of service | Stale or jumping feed continues to size risk | Feed integrity and quality gate |
| Elevation of privilege | A research role places an order or clears the kill switch alone | No trader role, paper-only mode, dual control |

`crypto-intel threats` prints the same map and fails closed if a named control
is missing from the catalog. No row describes how to attack an exchange, a
wallet, or this process.
