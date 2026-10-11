# Asset-class strategy notes

These rules are research heuristics. Each class has an edge hypothesis, an
entry, an invalidation, a horizon, and a size cap. They are not a promise of
return. Version 0.3 adds multi-horizon EMA alignment, breakout quality (volume +
range expansion), stablecoin velocity, tighter meme/perp filters, and stricter
RWA/DeFi liquidity/vol checks.

Regime labels, from `regime.py`:

- **trend**: eight-bar move of at least 2.5% and bar range under the stress band
- **range**: neither stress nor trend
- **stress**: average bar range at least 3.5% of price; directional ideas stand aside

## Major

Hypothesis: liquid majors trend when multi-horizon EMAs align and RSI is contained. Mean reversion only in range. Cap 8%. Horizon 20/8 bars. Cost 8 bps.

## Large-cap alt

Hypothesis: quality breakouts need volume >1.3x and range expansion outside stress. Cap 4%. Cost 14 bps.

## Stablecoin

Hypothesis: deviation and velocity of peg break are the monitors. No order. Cap 0%.

## DeFi

Hypothesis: calm-regime trend with liquidity proxy. Cap 2%. Cost 22 bps.

## Meme

Hypothesis: qualified burst requires volume acceleration and tighter extension filter. Cap 0.5%. Horizon 3 bars. Cost 45 bps.

## L2

Hypothesis: relative strength vs non-stress benchmark. Cap 3%. Cost 16 bps.

## RWA

Hypothesis: slow trend only with tighter gap and low-vol confirmation. Cap 2%. Horizon 24 bars. Cost 12 bps.

## Perpetual

Hypothesis: negative funding + tighter drift containment for carry; crowded + extension for research short fade. Cap 2%/1%. Cost 10 bps.

## Still out of scope

- Live order routing, withdrawal, and trade API keys.
- A broker adapter. That would be a separate human-approved system.
- Claims about future returns. Scores describe the synthetic fixture.

(See earlier version notes in git history for v0.4+ overlays, sleeves, and guards that sit on top of these base rules.)
