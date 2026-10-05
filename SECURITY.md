# Security policy

Report vulnerabilities privately through GitHub Security Advisories. Do not open a public issue with a secret or a wallet address.

In scope: the `crypto_intel` package, risk gate, audit log, and CI tripwires.
Out of scope: live trading profit claims. This repository cannot place live orders.

Supported branch: `main`.

Version 0.2 adds source attestation, feed integrity checks, and a role model that cannot enable live trading. See docs/security-architecture.md.

Version 0.11 adds session guards that cannot raise size, an information bulletin that is not an order, and a NIST CSF-style control map with no execution zone. See docs/v11-session-and-csf.md.
