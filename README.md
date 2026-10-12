# AIxTech crypto intel: paper-only trading information system

Research harness for automated cryptocurrency **information** and paper strategy
evaluation. It does not place live orders, does not store exchange secrets, and
is not financial advice.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![version](https://img.shields.io/badge/version-0.28.0-blue)
![mode](https://img.shields.io/badge/execution-paper%20only-orange)
![Licence](https://img.shields.io/badge/licence-MIT-green)

## What it does

- Classifies markets into eight asset classes and applies a different research rule to each.
- Labels each series trend, range, or stress, and stands aside in stress.
- Scores a signal, then a multi-layer risk gate (class caps, confidence floors, kill switch, drawdown, book overlay, confirmation passes) that can shrink or refuse it.
- Applies a declared round-trip cost by asset class in the paper backtest.
- Writes a hash-chained audit log, attests fixture sources, and redacts secret-like strings.
- Backtests on **synthetic** candles only. Network access is injectable and unused by default.

| Asset class | Research rule (core) | Risk cap | Cost |
|---|---|---|---|
| Major (BTC, ETH) | EMA trend outside stress; range-only RSI reversion + volume + multi-TF + ATR filter | 8% | 8 bps |
| Large-cap alt | Breakout with volume acceleration ≥1.5x + RSI guard, suppressed in stress | 4% | 14 bps |
| Stablecoin | 20 bp watch, 50 bp depeg alert. No order | 0% | n/a |
| DeFi | Trend only in a calm multi-TF, non-stress regime + volume-trend filter | 2% | 22 bps |
| Meme | Qualified burst with acceleration, chase filter, 3-bar horizon, stricter liquidity | 0.5% | 45 bps |
| L2 | Relative strength versus a non-stress, non-declining benchmark + ATR guard | 3% | 16 bps |
| RWA | Slow trend; halt on an 8% gap, stress, or thin participation / elevated vol | 2% | 12 bps |
| Perpetual | Negative-funding carry with persistence if drift is contained; crowded funding fade (paper short) | 2% / 1% | 10 bps |

Full notes: [docs/asset-class-strategies.md](docs/asset-class-strategies.md).
Security design: [docs/security-architecture.md](docs/security-architecture.md).
Latest enhancement layer: [docs/v28-adaptive-filters-and-redaction.md](docs/v28-adaptive-filters-and-redaction.md).

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
3. Class size caps, confidence floors, kill switch, drawdown halt, RWA gap halt, stress overlay, book exposure limits, multi-pass confirmation/sleeve/guard layers.
4. Hash-chained audit log, source attestation, feed jump and staleness checks, integrity digest helper.
5. PDPA-style tripwire over fixtures and docs.
6. Ruff lint (including bandit-style `S` rules), format, pytest coverage floor, gitleaks in CI.
7. Expanded secret redaction (API keys, wallets, emails, mnemonics, private-key markers, JWTs, Slack tokens, GitHub PATs, Discord tokens).

## Honesty

- No live exchange connector is included. Do not add trade keys to this tree.
- Strategy scores describe the synthetic fixture, not future returns.
- This is not legal, compliance, or investment advice.
