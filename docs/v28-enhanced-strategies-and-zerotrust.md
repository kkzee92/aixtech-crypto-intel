# Version 0.28: Enhanced strategies and zero-trust cyber/data security

This layer stays paper-only and research-only. It strengthens per-asset-class
heuristics and the control plane without adding live execution paths.

## Strategy enhancements

- **Major**: Added MACD histogram confirmation (fast-slow EMA difference) and
  Bollinger Band width filter to avoid low-volatility false trends. Size still
  capped at 8%.
- **Large-cap alt**: Added relative volume percentile and RSI divergence guard.
- **DeFi**: Multi-period realised-vol decay check.
- **Meme**: Added anti-pump social-proxy (volume spike without price follow-through).
- **L2**: Added 3-period relative strength consistency.
- **RWA**: Added participation score (volume / ATR).
- **Perpetual**: Added funding-rate moving average persistence window.
- **Stablecoin**: Tiered alerts with persistence (2-bar confirmation for depeg).

All enhancements can only reduce size or flatten; they never increase class caps.

## Cyber and data security architecture enhancements

- Expanded zero-trust continuous verification: every scan re-attests source
  digest and feed integrity before signal generation.
- Audit events now optionally carry a research-role tag and UTC timestamp
  (simulated; no external clock dependency in tests).
- Data minimization: classification now flags "derived signal" as research-only
  with short retention.
- Additional threat: AI/agent context poisoning via fixture injection. Control:
  mandatory SYNTHETIC label + digest mismatch aborts.
- Egress and secret refusal remain hard. No new credential loaders.
- Incident playbook adds "attestation digest mismatch" as an automatic kill-switch
  trigger in research mode.

See updated `strategies.py`, `security.py`, and `security-architecture.md`.

This remains not financial advice, not a production security product, and not
live trading infrastructure.
