# AIxTech crypto intel: paper-only trading information system

Research harness for automated cryptocurrency **information** and paper strategy
evaluation. It does not place live orders, does not store exchange secrets, and
is not financial advice.

Reference style: [zeekiankok92/aixtech-agent-harness-demo](https://github.com/zeekiankok92/aixtech-agent-harness-demo)
(CI gates, PDPA tripwire, AI disclosure, human review). This repository is
published from the connected account `kkzee92` because that connector cannot
push to `zeekiankok92`.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![mode](https://img.shields.io/badge/execution-paper%20only-orange)
![Licence](https://img.shields.io/badge/licence-MIT-green)

## What it does

- Classifies markets into eight asset classes and applies a different research rule to each.
- Scores a signal, then a risk gate that can shrink or refuse it.
- Writes a hash-chained audit log and redacts secret-like strings.
- Backtests on **synthetic** candles only. Network access is injectable and unused by default.

| Asset class | Research rule | Risk cap |
|---|---|---|
| Major (BTC, ETH) | EMA trend, plus a washed-out RSI stabilisation rule | 8% |
| Large-cap alt | Breakout only with volume confirmation | 4% |
| Stablecoin | Depeg monitor. No directional order | 0% |
| DeFi | Trend only in a calm realised-vol regime | 2% |
| Meme | Burst only if a liquidity proxy clears; 3-bar horizon | 0.5% |
| L2 | Relative strength versus a benchmark series | 3% |
| RWA | Slow trend; halt on an 8% gap | 2% |
| Perpetual | Negative-funding carry only if spot drift is contained | 2% |

Full notes: [docs/asset-class-strategies.md](docs/asset-class-strategies.md).
Security design: [docs/security-architecture.md](docs/security-architecture.md).

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/make_fixtures.py
PYTHONPATH=src python -m crypto_intel scan fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel demo fixtures/candles_synthetic.json
```

The fixture is labelled `SYNTHETIC` and is not a market history.

## Controls

1. Paper-only execution. `HALTED` and any live mode raise `PermissionError`.
2. Class size caps, confidence floors, kill switch, drawdown halt, RWA gap halt.
3. Hash-chained audit log with secret and wallet redaction.
4. PDPA-style tripwire over fixtures and docs.
5. Ruff lint (including bandit-style `S` rules), format, pytest coverage floor, gitleaks in CI.

## Honesty

- No live exchange connector is included. Do not add trade keys to this tree.
- Strategy scores describe the synthetic fixture, not future returns.
- This is not legal, compliance, or investment advice.
