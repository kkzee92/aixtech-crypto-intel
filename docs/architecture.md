# Architecture

```mermaid
flowchart LR
    FX["fixtures/candles_synthetic.json"] --> M["market.py"]
    M --> RG["regime.py"]
    M --> ST["strategies.py one rule per asset class"]
    RG --> ST
    ST --> RK["risk.py class caps + volatility scale"]
    CS["costs.py"] --> EN["engine.py paper fill"]
    RK --> EN
    EN --> AU["security.py hash-chained audit + timestamps"]
    PS["posture.py attestation and RBAC"] --> CLI["cli.py scan, brief, posture, backtest"]
    EN --> CLI
    BR["briefing.py"] --> CLI
```

Runtime dependencies are the Python standard library. Tests inject fetchers
and never open a socket. See [security-architecture.md](security-architecture.md)
and [asset-class-strategies.md](asset-class-strategies.md).

Version 0.3 adds ATR-based size scaling in the risk gate and UTC timestamps
inside the hashed audit detail. Paper-only constraints are unchanged.
