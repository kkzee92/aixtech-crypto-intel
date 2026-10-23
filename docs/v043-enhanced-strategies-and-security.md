# v0.43 Enhancements: Asset-class strategies and cyber/data security

Research-only updates. No live execution, no order routing, no secrets stored.

## Strategy enhancements per asset class

- **Major**: Added On-Balance Volume (OBV) proxy for volume confirmation on trend entries; Stochastic %K proxy for stronger mean-reversion in range regimes (oversold below 20).
- **Large-cap alt**: OBV rising required for breakout confirmation alongside existing multi-factor checks.
- **DeFi**: Volume confirmation tightened with OBV direction.
- **Meme**: Volume spike now also checks OBV acceleration to filter thin pumps.
- **Perpetual**: Funding stability check over last 3 bars (no sharp flips) before carry signal.
- **All classes**: Adaptive volatility scaling retained; new correlation risk note in briefing for multi-asset portfolios (research flag only).

These remain transparent heuristics on synthetic data. Scores describe the fixture, not future returns.

## Security architecture enhancements

- Simulated feed rate-limit control: research helper that flags excessive consecutive high-severity feed events (proxy for DoS or data-injection attempts).
- Expanded zero-trust: every input path (fixture, injected ticker) must pass source attestation + integrity digest before strategy evaluation.
- Audit lineage now includes a sealed optional flag for sensitive research notes (hash-only storage).
- Additional redaction coverage for cloud tokens and hardware seed approximations retained and documented.
- New control: portfolio-level correlation watch (if two majors both in stress, raise aggregate risk note).

## Updated threat model

| Threat | New/strengthened control |
|---|---|
| Volume-manipulated breakout | OBV proxy confirmation |
| Mean-reversion in trending regime | Stochastic + regime overlay |
| Feed flooding / injection | Rate-limit simulation + existing jump/staleness |
| Cross-asset correlation risk | Briefing correlation flag |
| Audit detail leakage | Optional sealed hash |

See updated `docs/asset-class-strategies.md` and `docs/security-architecture.md` for full notes.

**Honesty**: This is not financial advice, not a production trading system, and not a certified security product. Paper research only.
