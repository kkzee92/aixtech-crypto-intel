# Asset-class strategy notes

These rules are research heuristics. Each class has an edge hypothesis, an
entry, an invalidation, a horizon, and a size cap. They are not a promise of
return. Version 0.3 adds multi-factor confirmation, volatility-scaled sizing
(inversely proportional to recent ATR), and tighter filters.

Regime labels, from `regime.py`:

- **trend**: eight-bar move of at least 2.5% and bar range under the stress band
- **range**: neither stress nor trend
- **stress**: average bar range at least 3.5% of price; directional ideas stand aside

Volatility scaling: proposed size is reduced when recent 8-bar ATR exceeds a
target (default ~2%), so higher-volatility series take smaller paper risk.

## Major

Hypothesis: liquid majors trend often enough that a fast EMA above a slow EMA
is usable, unless RSI is stretched or the book is in stress. Mean reversion is
allowed only in a range regime. Version 0.3 requires positive short momentum
for the trend entry. Cap 8%. Horizon 8 or 20 bars. Research cost 8 bps round trip.
Size is vol-scaled.

## Large-cap alt

Hypothesis: breakouts without volume are noise, and stress-regime breakouts are
gap risk. Entry needs a close above the prior five-bar high, volume at least
1.3 times the recent average (tightened from 1.2x), and a non-stress regime.
Cap 4%. Cost 14 bps. Size is vol-scaled.

## Stablecoin

Hypothesis: the useful signal is a peg break. Deviation of 20 bps is a watch
alert. Deviation of 50 bps or more is a depeg alert. Risk gate forces size to
zero. Cost assumption is unused because no order is allowed.

## DeFi

Hypothesis: trend signals in high realised-volatility or stress regimes are
mostly gap risk. Stand aside if mean absolute return over 8 bars exceeds 6%
or the regime is stress. Version 0.3 also prefers volume above a recent average.
Cap 2%. Cost 22 bps. Size is vol-scaled.

## Meme

Hypothesis: most bursts are untradeable. A long is allowed only after a 15%
four-bar burst, rising volume, a volume floor, and an eight-bar extension that
is still under 35% (tightened from 40%). Horizon is 3 bars. Cap 0.5%. Cost 45 bps.
Size is vol-scaled.

## L2

Hypothesis: L2 tokens are bets on relative strength versus a benchmark. No
benchmark, or a benchmark in stress, means no trade. Version 0.3 also requires
own ATR to be contained. Cap 3%. Cost 16 bps. Size is vol-scaled.

## RWA

Hypothesis: tokenised real-world assets should be slow. An open-to-prior-close
gap above 8%, or a stress regime, halts the idea. Version 0.3 adds a short
momentum confirmation. Cap 2%, horizon 24 bars. Cost 12 bps. Size is vol-scaled.

## Perpetual

Hypothesis: negative funding with contained spot drift is a carry observation.
Funding at or above 10 bps is a crowded-funding alert, not a short. Drift
outside 4% blocks the carry even if funding is negative. Version 0.3 also
requires moderate ATR. Cap 2%. Cost 10 bps. Size is vol-scaled.
This does not model liquidation, funding intervals, or exchange risk.

## Still out of scope

- Live order routing, withdrawal, and trade API keys.
- A broker adapter. That would be a separate human-approved system.
- Claims about future returns. Scores describe the synthetic fixture.
