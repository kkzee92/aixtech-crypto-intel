# AIxTech crypto intel: paper-only trading information system

Research harness for automated cryptocurrency **information** and paper strategy
evaluation. It does not place live orders, does not store exchange secrets, and
is not financial advice.

Reference style: [zeekiankok92/aixtech-agent-harness-demo](https://github.com/zeekiankok92/aixtech-agent-harness-demo)
(CI gates, PDPA tripwire, AI disclosure, human review). This repository is
published from the connected account `kkzee92` because that connector cannot
push to `zeekiankok92`.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![version](https://img.shields.io/badge/version-0.21.0-blue)
![mode](https://img.shields.io/badge/execution-paper%20only-orange)
![Licence](https://img.shields.io/badge/licence-MIT-green)

## What it does

- Classifies markets into eight asset classes and applies a different research rule to each.
- Labels each series trend, range, or stress, and stands aside in stress.
- Scores a signal, then a risk gate that can shrink or refuse it.
- Applies a declared round-trip cost by asset class in the paper backtest.
- Writes a hash-chained audit log, attests fixture sources, and redacts secret-like strings.
- Scales paper sizes to a book gross cap and a crypto-beta cluster cap.
- Scores each asset class on the synthetic fixture after declared costs.
- Publishes a defensive control catalog, egress allowlist, and two-person kill-switch clear.
- v0.4 adds a data-quality gate, a per-class confirmation veto, volatility-targeted paper size, an LST sleeve cap, and read-key rotation / retention checks.
- v0.5 adds a cross-asset spillover and stablecoin-contagion overlay, an ETH/BTC relative sleeve inside majors, a chronological walk-forward split, data classification, and an executable STRIDE map.
- v0.6 adds a per-class enhancement that can only shrink paper size, a key-scope allowlist, a key-ceremony checklist, and an incident playbook that cannot resume live trading.
- v0.7 adds an offline information pipeline with class freshness SLAs, a third-pass sleeve per asset class, and a supply-chain / data-flow snapshot. Sleeves cannot raise size. Break-glass cannot enable live trading.
- v0.8 adds a fourth-pass overlay per asset class, a declared offline information cadence, and a data plane with no execution zone. Overlays cannot raise size.
- v0.9 adds a fifth-pass guard per asset class, an information alert router, and a zero-trust research plane. Guards cannot raise size. Alerts are not orders. Dual acknowledgement of a parameter digest cannot enable live trading.
- v0.10 adds a sixth-pass liquidity and structure guard per asset class, a breadth-aware information pack, and a cyber data-security plane with key separation and zero-retention credential and personal-data classes. Guards and the pack cannot raise size. There is still no execution zone.
- v0.11 adds a seventh-pass session guard per asset class, an offline information bulletin, and a NIST CSF 2.0-style control map. Guards and the bulletin cannot raise size. No role can trade or enable live trading. There is still no execution zone.
- v0.12 adds an eighth-pass basis and inventory guard per asset class, an offline information desk with a lineage digest, and a custody data-security plane. Guards and the desk cannot raise size. The withdrawal allowlist is empty. There is still no execution zone.
- v0.13 adds a ninth-pass venue-fragmentation guard per asset class, an offline information mesh, and a cyber-resilience plane. Guards and the mesh cannot raise size. Trade and withdrawal key scopes are refused. There is still no execution zone.
- v0.14 adds a tenth-pass decay guard per asset class, an offline information watchtower, and an evidence plane. Guards and the watchtower cannot raise size. The automation runner cannot read evidence or enable live trading. There is still no execution zone.
- v0.15 adds an eleventh-pass concentration guard per asset class, an offline information ledger, and a segregation plane. Guards and the ledger cannot raise size. Dual control of a research digest cannot enable live trading. There is still no execution zone.
- v0.16 adds a twelfth-pass correlation-break guard per asset class, an offline information radar, and a DLP egress plane. Guards and the radar cannot raise size. Secret, wallet, and personal-data strings are blocked before egress. There is still no execution zone.
- v0.17 adds a thirteenth-pass event-window guard per asset class, an offline information beacon, and an identity-bound research plane. Guards and the beacon cannot raise size. Sessions cannot be reused across roles. Trade and withdrawal scopes are refused. There is still no execution zone.
- v0.18 adds a fourteenth-pass participation guard per asset class, an offline information console, and a data-security plane. Guards and the console cannot raise size. There is still no execution zone.
- v0.19 adds a fifteenth-pass microstructure guard per asset class, an offline information tape, and a secrets-lifecycle plane. Guards and the tape cannot raise size. Trade, withdrawal, seed, and private-key scopes are refused. There is still no execution zone.
- v0.20 adds a sixteenth-pass inventory-age guard per asset class, an offline information dispatch, and a disclosure-boundary plane. Guards and the dispatch cannot raise size. A public brief drops paper size. There is still no execution zone.
- v0.21 adds a seventeenth-pass calendar and session guard per asset class, an offline research clock, and a data-residency plane. Guards and the clock cannot raise size. Research, audit, secret, and personal classes cannot leave the origin region. Encryption, audit-sign, and break-glass keys are separated and cannot trade. There is still no execution zone.
- Backtests on **synthetic** candles only. Network access is injectable and unused by default.

| Asset class | Research rule | Risk cap | Cost |
|---|---|---|---|
| Major (BTC, ETH) | EMA trend outside stress; range-only RSI reversion | 8% | 8 bps |
| Large-cap alt | Breakout with volume, suppressed in stress | 4% | 14 bps |
| Stablecoin | 20 bp watch, 50 bp depeg alert. No order | 0% | n/a |
| DeFi | Trend only in a calm, non-stress regime | 2% | 22 bps |
| Meme | Qualified burst, chase filter, 3-bar horizon | 0.5% | 45 bps |
| L2 | Relative strength versus a non-stress benchmark | 3% | 16 bps |
| RWA | Slow trend; halt on an 8% gap or stress | 2% | 12 bps |
| Perpetual | Negative-funding carry if drift is contained; crowded funding with extended drift is a 1% paper short fade | 2% / 1% short | 10 bps |

Full notes: [docs/asset-class-strategies.md](docs/asset-class-strategies.md).
Security design: [docs/security-architecture.md](docs/security-architecture.md).
v0.21 calendar guards and residency plane: [docs/v21-calendar-and-residency.md](docs/v21-calendar-and-residency.md).
Earlier passes remain in `docs/v06` through `docs/v20`.

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/make_fixtures.py
PYTHONPATH=src python -m crypto_intel scan fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel brief fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel posture fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel scorecard fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel controls
PYTHONPATH=src python -m crypto_intel v21 fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel clock fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel residency
PYTHONPATH=src python -m crypto_intel v20 fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel dispatch fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel boundary
PYTHONPATH=src python -m crypto_intel demo fixtures/candles_synthetic.json
```

The fixture is labelled `SYNTHETIC` and is not a market history.

## Controls

1. Paper-only execution. `HALTED` and any live mode raise `PermissionError`.
2. Trade and withdrawal credential names are refused. No role can place an order.
3. Class size caps, confidence floors, kill switch, drawdown halt, RWA gap halt, stress overlay.
4. Hash-chained audit log, source attestation, feed jump and staleness checks.
5. Book gross cap (12%) and crypto-beta cluster cap (10%). Stablecoins never take risk.
6. Egress allowlist and refused order or withdrawal paths. Dual-control kill-switch clear.
7. PDPA-style tripwire over fixtures and docs.
8. Ruff lint (including bandit-style `S` rules), format, pytest coverage floor, gitleaks in CI.
9. v0.4 quality gate, confirmation overlay, 90-day read-key rotation policy, and zero retention for secrets.
10. v0.5 cross-asset veto, major relative sleeve, data-class refusal, and STRIDE coverage check.
11. v0.6 class enhancement cannot raise size. Key scopes are market-read only. Incident recovery cannot enable live trading.
12. v0.7 pipeline is offline. Class sleeves cannot raise size. No role and no break-glass path can place an order or enable live trading.
13. v0.8 overlays cannot raise size. The data plane has no execution zone and refuses seeds, trade credentials, and personal data.
14. v0.9 guards cannot raise size. Alerts carry no order instruction. Zero-trust zones have no execution zone. Two acknowledgements of a parameter digest still cannot enable live trading.
15. v0.10 liquidity guards and the information pack cannot raise size. The cyber plane has no execution zone. Market-read, audit-sign, and break-glass keys cannot trade or enable live trading.
16. v0.11 session guards and the information bulletin cannot raise size. The CSF map has no execution zone. Researcher, auditor, and operator roles cannot trade or enable live trading.
17. v0.12 basis guards and the information desk cannot raise size. The custody plane has no execution zone. The withdrawal allowlist is empty. An operator cannot sign a research digest or enable live trading.
18. v0.13 fragmentation guards and the information mesh cannot raise size. The resilience plane has no execution zone. Trade and withdrawal scopes are refused. Backup restore cannot enable live trading. An operator cannot read the mesh.
19. v0.14 decay guards and the information watchtower cannot raise size. The evidence plane has no execution zone. Detection actions cannot enable live trading. The automation runner cannot read evidence. Evidence restore cannot enable live trading.
20. v0.15 concentration guards and the information ledger cannot raise size. The segregation plane has no execution zone. A researcher cannot append the audit log. An automation runner cannot read research records. Dual control cannot enable live trading.
21. v0.16 correlation guards and the information radar cannot raise size. The DLP plane has no execution zone. Secret, wallet, email, and phone-like strings are blocked before egress. An automation runner cannot emit a digest or enable live trading.
22. v0.17 event-window guards and the information beacon cannot raise size. The identity plane has no execution zone. A session cannot be reused across roles. Trade, withdrawal, and seed scopes are refused. An automation runner cannot mint a session or enable live trading.
23. v0.21 calendar guards and the research clock cannot raise size. The residency plane has no execution zone. Research, audit, secret, and personal classes cannot cross a region boundary. Encryption, audit-sign, and break-glass keys are separated and cannot trade or enable live trading.

## Honesty

- No live exchange connector is included. Do not add trade keys to this tree.
- Strategy scores describe the synthetic fixture, not future returns.
- This is not legal, compliance, or investment advice.
