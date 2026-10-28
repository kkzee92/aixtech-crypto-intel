# Security architecture

Version 0.48 extends the control plane with portfolio risk aggregation and simulated multi-party attestation. It is still a research design, not a
certified security product and not legal advice.

## Trust boundaries

```mermaid
flowchart LR
    F["Synthetic fixture or injected public ticker"] --> AT["Source attestation (multi-party sealed)"]
    AT --> S["Strategy research rules plus regime + portfolio overlay"]
    S --> R["Risk gate: class caps, kill switch, drawdown, volatility scale, portfolio VaR/HHI"]
    R --> P["Paper fill only"]
    P --> A["Hash-chained audit log with timestamps and dual-control notes"]
    K["Trade or withdrawal keys"] -.-> X["Refused. Never loaded"]
    RBAC["Researcher, auditor, operator"] --> R
```

The system has no order router. `assert_paper_only` refuses any mode other than
`PAPER`. `refuse_trade_secret` rejects names that look like trade, withdraw,
transfer, or order credentials. Roles cannot enable live trading.

## Roles

| Role | Allowed | Denied |
|---|---|---|
| Researcher | scan, backtest, read audit | place order, withdraw, enable live |
| Auditor | read audit, verify chain, scan | place order, withdraw, enable live |
| Operator | scan, kill switch, read audit | place order, withdraw, enable live |

There is no trader role. Promoting a signal to a broker is a separate system. Dual acknowledgment preferred for high-impact actions.

## Data classes

| Field | Class | Handling |
|---|---|---|
| Symbol, OHLCV | Public market | Synthetic in this repo |
| Funding rate | Public market | Research feature only |
| Portfolio risk features | Derived public | Synthetic computation only |
| Source label | Integrity | Must be SYNTHETIC or PUBLIC_READ |
| Read-only market key | Secret, optional | Name must say read, market, or public. Never logged |
| Trade or withdrawal key | Secret | Refused |
| Private key / mnemonic | Secret | Refused, redacted |
| Wallet address | Sensitive identifier | Redacted, banned from fixtures |
| Email, NRIC, phone | Personal | Tripwire in `scripts/check_pdpa.py` |
| Solana-style key / multi-sig share | Secret | Refused, redacted |

PDPA note: the tripwire is not a data-loss-prevention product. A production
deployment still needs access control, vendor review, and a human DPO decision.
Wallet addresses can be personal data depending on context; this repo does not
store them.

## Feed integrity

`feed_status` flags a non-positive price, a print older than 15 minutes, or a
jump above 25% versus the prior print. Tests inject the payload. The default
path does not open a socket.

`attest_source` hashes the label plus body so a fixture swap changes the digest.
The loader still rejects anything that is not labelled SYNTHETIC.
`integrity_digest` provides a SHA-256 helper for research payloads. Simulated multi-party sealed digest available.

## Threats and controls

| Threat | Control |
|---|---|
| Secret committed | gitleaks CI, expanded redaction patterns (incl. Solana, multi-sig, HW QR), no key loader |
| Trade key pasted into config | `refuse_trade_secret` |
| Strategy injection via fixture | SYNTHETIC label required, source attestation (multi-party) |
| Stale or jumped public ticker | feed status watch or high |
| Oversized risk on thin assets or portfolio | Per-class cap, confidence floor, class cost, volatility scaling, VWAP/volume, portfolio VaR/HHI filters |
| Runaway loss | Drawdown halt and kill switch |
| Audit tamper | SHA-256 chain over sequence, action, timestamped detail |
| Live-order mistake | No live client; mode guard; RBAC deny |
| Personal data in agent context | AGENTS.md ban plus CI tripwire |
| Privilege creep | No role can place an order |
| Solana key or multi-sig paste | Base58 / pattern + redaction |

## Incident handling

1. Engage the kill switch. New paper size goes to zero.
2. Freeze the audit chain and record the source attestation digest.
3. If a secret was pasted, rotate it outside this repo and purge it from history.
4. Do not open a public issue that contains a secret or a wallet address.
5. A human (preferably dual) reviews before the kill switch is cleared.

## Operating rules

- Market-data credentials, if ever added, stay read-only and separate from any future trade credential.
- Logs pass through `redact` before they are stored.
- Default deployment is research. Promoting a signal to a broker is a separate, human-approved system.
- Portfolio computations and multi-party notes remain research-only.
