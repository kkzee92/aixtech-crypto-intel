# AIxTech crypto intel: paper-only trading information system

Research harness for automated cryptocurrency **information** and paper strategy
evaluation. It does not place live orders, does not store exchange secrets, and
is not financial advice.

Reference style: [zeekiankok92/aixtech-agent-harness-demo](https://github.com/zeekiankok92/aixtech-agent-harness-demo)
(CI gates, PDPA tripwire, AI disclosure, human review). This repository is
published from the connected account `kkzee92` because that connector cannot
push to `zeekiankok92`. The public reference remains under zeekiankok92.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![version](https://img.shields.io/badge/version-0.11.0-blue)
![mode](https://img.shields.io/badge/execution-paper%20only-orange)
![Licence](https://img.shields.io/badge/licence-MIT-green)

## v0.11 enhancements

- Multi-timeframe slope alignment proxy for trend confirmation on Major and Large-cap alt.
- Expanded secret redaction (Solana-style base58, longer hex keys) and funding jump in anomaly scoring.
- Data resilience notes (encryption at rest, residency) and reinforced zero-trust re-validation.
- Documentation and version updated. Still paper-only, research-only.

Full notes: [docs/v35-enhanced-mtf-and-resilience.md](docs/v35-enhanced-mtf-and-resilience.md).

## What it does

- Classifies markets into eight asset classes and applies a different research rule to each.
- Labels each series trend, range, or stress, and stands aside in stress.
- Scores a signal with multi-factor confirmation (EMA alignment, MACD-style momentum, adaptive RSI/stochastic, volume, Bollinger-style envelopes, trend strength proxy, volatility-scaled sizing, median volume, multi-window, correlation proxy, divergence, VWAP, MTF slope), then a risk gate that can shrink or refuse it.
- Applies a declared round-trip cost by asset class in the paper backtest.
- Writes a hash-chained audit log, attests fixture sources, redacts secret-like strings (expanded patterns including private keys, seeds, tokens, PATs, PEM, Discord, Google, hex, Telegram, Solana), and provides series integrity digests plus enhanced anomaly scoring.
- Backtests on **synthetic** candles only. Network access is injectable and unused by default.

| Asset class | Research rule | Risk cap | Cost |
|---|---|---|---|
| Major (BTC, ETH) | Multi-EMA + MACD + adaptive RSI/stochastic + BB envelope + trend strength + short slope + divergence/VWAP + MTF alignment outside stress; range-only deep RSI/stochastic reversion; vol-scaled | 8% | 8 bps |
| Large-cap alt | Breakout with median-based adaptive volume + multi-bar + MACD + strength + stochastic + VWAP + MTF, suppressed in stress; vol-scaled | 4% | 14 bps |
| Stablecoin | Adaptive 30-60 bp watch, 60-90 bp depeg alert (with sustained check). No order | 0% | n/a |
| DeFi | Trend only in a calm, non-stress regime with median volume, momentum, strength, stochastic, divergence; vol-scaled | 2% | 22 bps |
| Meme | Qualified burst with tighter adaptive extension, volume accel, RSI/stochastic filter, consistency, median floor; vol-scaled | 0.5% | 45 bps |
| L2 | Relative strength versus a non-stress benchmark with ATR contained, median relative volume, own strength, correlation proxy, multi-window excess; vol-scaled | 3% | 16 bps |
| RWA | Slow trend + momentum + strength + stochastic; halt on adaptive gap or stress; vol-scaled | 2% | 12 bps |
| Perpetual | Negative-funding carry if drift (ATR-scaled), ATR, multi-print stability, contained strength and stochastic, funding trend; crowded funding is an alert; vol-scaled | 2% | 10 bps |

Full notes: [docs/asset-class-strategies.md](docs/asset-class-strategies.md).  
Latest enhancement log: [docs/v35-enhanced-mtf-and-resilience.md](docs/v35-enhanced-mtf-and-resilience.md).  
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
2. Trade and withdrawal credential names are refused. No role can place an order. Key separation enforced in design.
3. Class size caps, confidence floors, kill switch, drawdown halt, RWA gap halt, stress overlay, volatility-scaled sizing.
4. Hash-chained audit log, source attestation, series integrity digest, feed jump and staleness checks, expanded secret redaction, enhanced anomaly scoring, timestamp freshness helper, series consistency check.
5. PDPA-style tripwire over fixtures and docs.
6. Ruff lint (including bandit-style `S` rules), format, pytest coverage floor, gitleaks in CI.

## Honesty

- No live exchange connector is included. Do not add trade keys to this tree.
- Strategy scores describe the synthetic fixture, not future returns.
- This is not legal, compliance, or investment advice.
