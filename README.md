# AIxTech crypto intel: paper-only trading information system

Research harness for automated cryptocurrency **information** and paper strategy
evaluation. It does not place live orders, does not store exchange secrets, and
is not financial advice.

Reference style: [zeekiankok92/aixtech-agent-harness-demo](https://github.com/zeekiankok92/aixtech-agent-harness-demo)
(CI gates, PDPA tripwire, AI disclosure, human review). This repository is
published from the connected account `kkzee92` because that connector cannot
push to `zeekiankok92`.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![version](https://img.shields.io/badge/version-0.8.0-blue)
![mode](https://img.shields.io/badge/execution-paper%20only-orange)
![Licence](https://img.shields.io/badge/licence-MIT-green)

## v0.8 enhancements

- Median-based volume confirmations for robustness against spikes (alts, DeFi, meme, L2).
- Multi-window EMA slope confirmation for majors.
- Multi-print funding stability for perpetuals.
- Expanded secret redaction (GitHub PATs, PEM headers) and series anomaly scoring helper.
- Documentation and version updated. Still paper-only, research-only.

Full notes: [docs/v32-enhanced-robustness-and-cyber.md](docs/v32-enhanced-robustness-and-cyber.md).

## What it does

- Classifies markets into eight asset classes and applies a different research rule to each.
- Labels each series trend, range, or stress, and stands aside in stress.
- Scores a signal with multi-factor confirmation (EMA alignment, MACD-style momentum, adaptive RSI/volume, Bollinger-style envelopes, trend strength proxy, volatility-scaled sizing, median volume, multi-window), then a risk gate that can shrink or refuse it.
- Applies a declared round-trip cost by asset class in the paper backtest.
- Writes a hash-chained audit log, attests fixture sources, redacts secret-like strings (expanded patterns including private keys, seeds, tokens, PATs, PEM), and provides series integrity digests plus anomaly scoring.
- Backtests on **synthetic** candles only. Network access is injectable and unused by default.

| Asset class | Research rule | Risk cap | Cost |
|---|---|---|---|
| Major (BTC, ETH) | Multi-EMA + MACD + adaptive RSI + BB envelope + trend strength + short slope outside stress; range-only deep RSI reversion; vol-scaled | 8% | 8 bps |
| Large-cap alt | Breakout with median-based adaptive volume + multi-bar + MACD + strength, suppressed in stress; vol-scaled | 4% | 14 bps |
| Stablecoin | Adaptive 30-60 bp watch, 60-90 bp depeg alert (with sustained check). No order | 0% | n/a |
| DeFi | Trend only in a calm, non-stress regime with median volume, momentum, strength; vol-scaled | 2% | 22 bps |
| Meme | Qualified burst with tighter adaptive extension, volume accel, RSI filter, consistency, median floor; vol-scaled | 0.5% | 45 bps |
| L2 | Relative strength versus a non-stress benchmark with ATR contained, median relative volume, own strength; vol-scaled | 3% | 16 bps |
| RWA | Slow trend + momentum + strength; halt on adaptive gap or stress; vol-scaled | 2% | 12 bps |
| Perpetual | Negative-funding carry if drift (ATR-scaled), ATR, multi-print stability, contained strength; crowded funding is an alert; vol-scaled | 2% | 10 bps |

Full notes: [docs/asset-class-strategies.md](docs/asset-class-strategies.md).  
Latest enhancement log: [docs/v32-enhanced-robustness-and-cyber.md](docs/v32-enhanced-robustness-and-cyber.md).  
Security design: [docs/security-architecture.md](docs/security-architecture.md).

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
3. Class size caps, confidence floors, kill switch, drawdown halt, RWA gap halt, stress overlay, volatility-scaled sizing.
4. Hash-chained audit log, source attestation, series integrity digest, feed jump and staleness checks, expanded secret redaction, anomaly scoring helper.
5. PDPA-style tripwire over fixtures and docs.
6. Ruff lint (including bandit-style `S` rules), format, pytest coverage floor, gitleaks in CI.

## Honesty

- No live exchange connector is included. Do not add trade keys to this tree.
- Strategy scores describe the synthetic fixture, not future returns.
- This is not legal, compliance, or investment advice.
