# Data classification

The research system accepts three labels and refuses two.

| Label contains | Class | Retention | Handling |
|---|---|---|---|
| `SYNTHETIC` | Synthetic | Fixture, no operational expiry | Allowed. Must stay labelled |
| `PUBLIC` | Public market | 30 days if an operational cache is added later | Allowed. Read-only market data |
| `AUDIT` | Operational audit | 365 days | Allowed. Redacted before storage |
| `NRIC`, `email`, `phone`, `passport` | Personal | 0 | Refused |
| `secret`, `api_key`, `private_key`, `seed` | Secret | 0 | Refused |

Unlabelled payloads raise `ValueError`. Personal and secret labels raise
`PermissionError` even if the caller intended them as research input. This is
the same PDPA-style boundary as the AIxTech agent harness: production personal
data does not enter the agent or fixture context. It is a tripwire, not legal
advice and not a full data-loss-prevention control.
