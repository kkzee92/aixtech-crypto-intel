# Architecture

```mermaid
flowchart LR
    FX["fixtures/candles_synthetic.json"] --> M["market.py"]
    M --> RG["regime.py"]
    M --> ST["strategies.py one rule per asset class"]
    RG --> ST
    ST --> RK["risk.py"]
    CS["costs.py"] --> EN["engine.py paper fill"]
    RK --> EN
    EN --> AU["security.py audit chain"]
    PS["posture.py attestation and RBAC"] --> CLI["cli.py scan, brief, posture, backtest"]
    EN --> CLI
    BR["briefing.py"] --> CLI
```

Runtime dependencies are the Python standard library. Tests inject fetchers
and never open a socket. See [security-architecture.md](security-architecture.md)
and [asset-class-strategies.md](asset-class-strategies.md).
