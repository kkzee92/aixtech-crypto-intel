# Architecture

```mermaid
flowchart LR
    FX["fixtures/candles_synthetic.json"] --> M["market.py"]
    M --> Q["quality.py"]
    M --> RG["regime.py"]
    M --> ST["strategies.py one rule per asset class"]
    RG --> ST
    ST --> CF["confirm.py second check"]
    ST --> RK["risk.py"]
    CF --> IN["intel.py informed paper report"]
    Q --> IN
    RK --> IN
    SZ["sizing.py vol target and LST cap"] --> IN
    CS["costs.py"] --> EN["engine.py paper fill"]
    RK --> EN
    EN --> AU["security.py audit chain"]
    CU["custody.py rotation and retention"] --> CLI["cli.py"]
    PS["posture.py attestation and RBAC"] --> CLI
    IN --> CLI
    EN --> CLI
    BR["briefing.py"] --> CLI
```

`scan` and `backtest` keep the v0.3 paper path. `intel` is the v0.4 information path: quality, confirmation, and volatility targeting. Neither path can place a live order.

Runtime dependencies are the Python standard library. Tests inject fetchers and never open a socket. See [security-architecture.md](security-architecture.md), [data-security-architecture.md](data-security-architecture.md), and [asset-class-strategies.md](asset-class-strategies.md).
