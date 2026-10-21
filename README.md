# AIxTech crypto intel: paper-only trading information system

Research harness for automated cryptocurrency **information** and paper strategy
evaluation. It does not place live orders, does not store exchange secrets, and
is not financial advice.

**Latest enhanced version**: [aixtech-crypto-intel-v018](https://github.com/kkzee92/aixtech-crypto-intel-v018) with Parabolic SAR proxies, volume profile refinements, multi-asset correlation regimes, advanced Merkle-style lineage, isolation anomaly, and expanded zero-trust/data residency.

Reference style: [zeekiankok92/aixtech-agent-harness-demo](https://github.com/zeekiankok92/aixtech-agent-harness-demo)
(CI gates, PDPA tripwire, AI disclosure, human review). This repository is
published from the connected account `kkzee92` because that connector cannot
push to `zeekiankok92`. The public reference remains under zeekiankok92.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![version](https://img.shields.io/badge/version-0.16.0-blue)
![mode](https://img.shields.io/badge/execution-paper%20only-orange)
![Licence](https://img.shields.io/badge/licence-MIT-green)

## v0.16 enhancements

- Added ADX-style directional movement proxy as trend strength confirmation for Major, Large-cap alt, DeFi, and RWA strategies.
- Enhanced data residency and cross-border transfer notes in the security architecture.
- Refined anomaly scoring with directional inconsistency checks.
- Explicit zero-trust re-validation including ADX consistency.
- Still strictly paper-only, research-only.

Full notes: [docs/v39-enhanced-adx-and-residency.md](docs/v39-enhanced-adx-and-residency.md).

## v0.15 enhancements

- Added Williams %R (14) as fast momentum confirmation for Major and Large-cap alt strategies.
- Anomaly scoring refined with extreme oscillator readings and multi-oscillator divergence.
- Explicit zero-trust re-validation and production encryption / key-management notes.
- Still strictly paper-only, research-only.

Full notes: [docs/v38-enhanced-williams-and-zerotrust.md](docs/v38-enhanced-williams-and-zerotrust.md).

## What it does

- Classifies markets into eight asset classes and applies a different research rule to each.
- Labels each series trend, range, or stress, and stands aside in stress.
- Scores a signal with multi-factor confirmation (EMA alignment, MACD-style momentum, adaptive RSI/stochastic, volume, Bollinger-style envelopes, trend strength proxy, ADX-style directional movement, volatility-scaled sizing, median/IQR volume, multi-window, correlation proxy, divergence, VWAP, MTF slope, support/resistance, CCI, Williams %R), then a risk gate that can shrink or refuse it.
- Applies a declared round-trip cost by asset class in the paper backtest.
- Writes a hash-chained audit log, attests fixture sources, redacts secret-like strings (expanded patterns including private keys, seeds, tokens, PATs, PEM, Discord, Google, hex, Telegram, Solana, additional base58/WIF), and provides series integrity digests plus enhanced anomaly scoring.
- Backtests on **synthetic** candles only. Network access is injectable and unused by default.

| Asset class | Research rule | Risk cap | Cost |
|---|---|---|---|
| Major (BTC, ETH) | Multi-EMA + MACD + adaptive RSI/stochastic + BB envelope + trend strength + ADX-style + short slope + divergence/VWAP + OBV + MTF + S/R + CCI + Williams %R alignment outside stress; range-only deep RSI/stochastic reversion; vol-scaled | 8% | 8 bps |
| Large-cap alt | Breakout with robust volume + multi-bar + MACD + strength + ADX-style + stochastic + VWAP + OBV + MTF + S/R + CCI + Williams %R, suppressed in stress; vol-scaled | 4% | 14 bps |
| Stablecoin | Adaptive 30-60 bp watch, 60-90 bp depeg alert (with sustained check). No order | 0% | n/a |
| DeFi | Trend only in a calm, non-stress regime with robust volume, momentum, strength, ADX-style, stochastic, divergence, MTF; vol-scaled | 2% | 22 bps |
| Meme | Qualified burst with tighter adaptive extension, volume accel, RSI/stochastic filter, consistency, robust median floor; vol-scaled | 0.5% | 45 bps |
| L2 | Relative strength versus a non-stress benchmark with ATR contained, robust relative volume, own strength, correlation proxy, multi-window excess; vol-scaled | 3% | 16 bps |
| RWA | Slow trend + momentum + strength + ADX-style + stochastic + MTF; halt on adaptive gap or stress; vol-scaled | 2% | 12 bps |
| Perpetual | Negative-funding carry if drift (ATR-scaled), ATR, multi-print stability, contained strength and stochastic, funding trend consistency; crowded funding is an alert; vol-scaled | 2% | 10 bps |

Full notes: [docs/asset-class-strategies.md](docs/asset-class-strategies.md).  
Latest enhancement log: [docs/v39-enhanced-adx-and-residency.md](docs/v39-enhanced-adx-and-residency.md).  
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
4. Hash-chained audit log, source attestation, series integrity digest, feed jump and staleness checks, expanded secret redaction, enhanced anomaly scoring, timestamp freshness helper, series consistency check, ADX consistency.
5. PDPA-style tripwire over fixtures and docs.
6. Ruff lint (including bandit-style `S` rules), format, pytest coverage floor, gitleaks in CI.

## Honesty

- No live exchange connector is included. Do not add trade keys to this tree.
- Strategy scores describe the synthetic fixture, not future returns.
- This is not legal, compliance, or investment advice.
