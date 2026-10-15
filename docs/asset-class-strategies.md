# Asset-class strategy notes

These rules are research heuristics. Each class has an edge hypothesis, an
entry, an invalidation, a horizon, and a size cap. They are not a promise of
return. Version 0.6 adds Bollinger-style envelope confirmation for majors,
minor adaptive refinements across classes, and continues multi-factor logic
from 0.5 (MACD-style momentum, adaptive thresholds based on volatility, tighter
filters, refined volume and RSI logic). Size remains volatility-scaled.

Regime labels, from `regime.py`:

- **trend**: eight-bar move of at least 2.5% and bar range under the stress band
- **range**: neither stress nor trend
- **stress**: average bar range at least 3.5% of price; directional ideas stand aside

Volatility scaling: proposed size is reduced when recent 8-bar ATR exceeds a
target (default ~2%), so higher-volatility series take smaller paper risk.

## Major

Hypothesis: liquid majors trend often enough that multi-EMA alignment plus MACD-style
momentum confirmation and Bollinger-style envelope is usable, unless RSI is stretched (adaptive band) or the book is in stress.
Mean reversion is allowed only in a range regime with washed-out adaptive RSI.
Cap 8%. Horizon 8 or 20 bars. Research cost 8 bps round trip. Size is vol-scaled.

## Large-cap alt

Hypothesis: breakouts without volume are noise, and stress-regime breakouts are
gap risk. Entry needs a close above the prior five-bar high, volume at least
adaptive multiple of recent average, positive multi-bar momentum, MACD confirmation,
and a non-stress regime. Cap 4%. Cost 14 bps. Size is vol-scaled.

## Stablecoin

Hypothesis: the useful signal is a peg break. Adaptive deviation bands for watch
and depeg alerts. Risk gate forces size to zero. Cost assumption is unused because no order is allowed.

## DeFi

Hypothesis: trend signals in high realised-volatility or stress regimes are
mostly gap risk. Stand aside if mean absolute return over 8 bars exceeds adaptive
limit or the regime is stress. Prefer volume support and positive momentum.
Cap 2%. Cost 22 bps. Size is vol-scaled.

## Meme

Hypothesis: most bursts are untradeable. A long is allowed only after a qualified
burst, rising volume with acceleration, volume floor, extension under adaptive
limit, and RSI not overbought. Horizon is 3 bars. Cap 0.5%. Cost 45 bps.
Size is vol-scaled.

## L2

Hypothesis: L2 tokens are bets on relative strength versus a benchmark. No
benchmark, or a benchmark in stress, means no trade. Require excess return,
own ATR contained, and relative volume preference. Cap 3%. Cost 16 bps. Size is vol-scaled.

## RWA

Hypothesis: tokenised real-world assets should be slow. An open-to-prior-close
gap above adaptive limit, or a stress regime, halts the idea. Add momentum confirmation.
Cap 2%, horizon 24 bars. Cost 12 bps. Size is vol-scaled.

## Perpetual

Hypothesis: negative funding with contained spot drift, moderate ATR, and stable
funding is a carry observation. Funding at or above 10 bps is a crowded-funding alert.
Drift outside adaptive limit blocks the carry. Cap 2%. Cost 10 bps. Size is vol-scaled.
This does not model liquidation, funding intervals, or exchange risk.

## Still out of scope

- Live order routing, withdrawal, and trade API keys.
- A broker adapter. That would be a separate human-approved system.
- Claims about future returns. Scores describe the synthetic fixture.

See also [v30-multi-factor-and-resilience.md](v30-multi-factor-and-resilience.md).
