# AIxTech crypto intel: paper-only trading information system

Research harness for automated cryptocurrency **information** and paper strategy
evaluation. It does not place live orders, does not store exchange secrets, and
is not financial advice.

Reference style: [zeekiankok92/aixtech-agent-harness-demo](https://github.com/zeekiankok92/aixtech-agent-harness-demo)
(CI gates, PDPA tripwire, AI disclosure, human review). This repository is
published from the connected account `kkzee92` because that connector cannot
push to `zeekiankok92`.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![version](https://img.shields.io/badge/version-0.5.0-blue)
![mode](https://img.shields.io/badge/execution-paper%20only-orange)
![Licence](https://img.shields.io/badge/licence-MIT-green)

## What it does

- Classifies markets into eight asset classes and applies a different research rule to each.
- Labels each series trend, range, or stress, and stands aside in stress.
- Scores a signal with multi-factor confirmation (including MACD-style momentum for majors), adaptive volume thresholds, multi-bar consistency, and volatility-scaled sizing, then a risk gate that can shrink or refuse it.
- Applies a declared round-trip cost by asset class in the paper backtest.
- Writes a hash-chained audit log, attests fixture sources, redacts secret-like strings (including private-key and seed proxies), and provides series integrity digests.
- Backtests on **synthetic** candles only and returns equity, win rate, and a simple Sharpe proxy. Network access is injectable and unused by default.

| Asset class | Research rule | Risk cap | Cost |
|---|---|---|---|
| Major (BTC, ETH) | EMA + MACD hist + RSI outside stress; range-only deep RSI reversion; vol-scaled | 8% | 8 bps |
| Large-cap alt | Breakout with 1.4x volume + multi-bar confirmation, suppressed in stress; vol-scaled | 4% | 14 bps |
| Stablecoin | 40 bp watch, 80 bp depeg alert. No order | 0% | n/a |
| DeFi | Trend only in a calm (<=5.5% realised), non-stress regime with volume support; vol-scaled | 2% | 22 bps |
| Meme | Qualified 12% 3-bar burst, tighter chase, 3-bar horizon; vol-scaled | 0.5% | 45 bps |
| L2 | Relative strength (>=3.5%) versus a non-stress benchmark, ATR contained; vol-scaled | 3% | 16 bps |
| RWA | Slow trend + momentum; halt on a 7% gap or stress; vol-scaled | 2% | 12 bps |
| Perpetual | Negative-funding carry if drift and ATR contained; crowded funding is an alert; vol-scaled | 2% | 10 bps |

Full notes: [docs/asset-class-strategies.md](docs/asset-class-strategies.md).
Security design: [docs/security-architecture.md](docs/security-architecture.md).
Enhancement log: [docs/v30-further-strategy-and-security-enhancements.md](docs/v30-further-strategy-and-security-enhancements.md).

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/make_fixtures.py
PYTHONPATH=src python -m crypto_intel scan fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel brief fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel posture fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel demo fixtures/candles_synthetic.json
```

The fixture is labelled `SYNTHETIC` and is not a market history.

## Controls

1. Paper-only execution. `HALTED` and any live mode raise `PermissionError`.
2. Trade and withdrawal credential names are refused. No role can place an order.
3. Class size caps, confidence floors, kill switch, drawdown halt, RWA gap halt, stress overlay, ATR-based size reduction.
4. Hash-chained audit log, source attestation, series integrity digest, feed jump and staleness checks, expanded secret redaction.
5. PDPA-style tripwire over fixtures and docs.
6. Ruff lint (including bandit-style `S` rules), format, pytest coverage floor, gitleaks in CI.

## Honesty

- No live exchange connector is included. Do not add trade keys to this tree.
- Strategy scores describe the synthetic fixture, not future returns.
- This is not legal, compliance, or investment advice.
