# AIxTech crypto intel: paper-only trading information system

Research harness for automated cryptocurrency **information** and paper strategy
evaluation. It does not place live orders, does not store exchange secrets, and
is not financial advice.

Reference style: [zeekiankok92/aixtech-agent-harness-demo](https://github.com/zeekiankok92/aixtech-agent-harness-demo)
(CI gates, PDPA tripwire, AI disclosure, human review). This repository is
published from the connected account `kkzee92` because that connector cannot
push to `zeekiankok92`.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![version](https://img.shields.io/badge/version-0.22.0-blue)
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
- v0.4 through v0.21 remain in force. See the version notes below and `docs/`.
- v0.22 adds an eighteenth-pass depth-quality guard per asset class, an offline custody-chain digest, and a provenance plane. Guards and the digest cannot raise size. Only SYNTHETIC or PUBLIC_READ labels can be attested. Trade, withdrawal, seed, and private-key scopes cannot attest. Secret and personal classes cannot enter a published handoff. There is still no execution zone.
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
v0.22 depth guards and provenance plane: [docs/v22-depth-and-provenance.md](docs/v22-depth-and-provenance.md).
Earlier passes remain in `docs/v06` through `docs/v21`.

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/make_fixtures.py
PYTHONPATH=src python -m crypto_intel scan fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel brief fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel posture fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel v22 fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel chain fixtures/candles_synthetic.json
PYTHONPATH=src python -m crypto_intel provenance
PYTHONPATH=src python -m crypto_intel demo fixtures/candles_synthetic.json
```

The fixture is labelled `SYNTHETIC` and is not a market history.

## Controls

1. Paper-only execution. `HALTED` and any live mode raise `PermissionError`.
2. Trade and withdrawal credential names are refused. No role can place an order.
3. Class size caps, confidence floors, kill switch, drawdown halt, RWA gap halt, stress overlay.
4. Hash-chained audit log, source attestation, feed jump and staleness checks.
5. Book gross cap and crypto-beta cluster cap. Stablecoins never take risk.
6. v0.22 depth guards and the custody-chain digest cannot raise size. The provenance plane has no execution zone. Only SYNTHETIC or PUBLIC_READ labels can be attested. Trade, withdrawal, seed, and private-key scopes cannot attest or enable live trading.
7. PDPA-style tripwire over fixtures and docs.
8. Ruff lint (including bandit-style `S` rules), format, pytest coverage floor, gitleaks in CI.

Earlier control notes for v0.4 through v0.21 stay in git history and `docs/`.

## Honesty

- No live exchange connector is included. Do not add trade keys to this tree.
- Strategy scores describe the synthetic fixture, not future returns.
- This is not legal, compliance, or investment advice.
