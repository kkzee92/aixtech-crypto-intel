# Asset-class strategy notes

These rules are research heuristics. Each class has an edge hypothesis, an
entry, an invalidation, a horizon, and a size cap. They are not a promise of
return. Version 0.2 adds a shared regime overlay and class cost assumptions.
Version 0.3 adds a versioned parameter catalog, a book exposure overlay, and a
paper short fade for crowded perpetual funding.

Regime labels, from `regime.py`:

- **trend**: eight-bar move of at least 2.5% and bar range under the stress band
- **range**: neither stress nor trend
- **stress**: average bar range at least 3.5% of price; directional ideas stand aside

## Major

Hypothesis: liquid majors trend often enough that a fast EMA above a slow EMA
is usable, unless RSI is stretched or the book is in stress. Mean reversion is
allowed only in a range regime. Cap 8%. Horizon 8 or 20 bars. Research cost
8 bps round trip.

## Large-cap alt

Hypothesis: breakouts without volume are noise, and stress-regime breakouts are
gap risk. Entry needs a close above the prior five-bar high, volume at least
1.2 times the recent average, and a non-stress regime. Cap 4%. Cost 14 bps.

## Stablecoin

Hypothesis: the useful signal is a peg break. Deviation of 20 bps is a watch
alert. Deviation of 50 bps or more is a depeg alert. Risk gate forces size to
zero. Cost assumption is unused because no order is allowed.

## DeFi

Hypothesis: trend signals in high realised-volatility or stress regimes are
mostly gap risk. Stand aside if mean absolute return over 8 bars exceeds 6%
or the regime is stress. Cap 2%. Cost 22 bps.

## Meme

Hypothesis: most bursts are untradeable. A long is allowed only after a 15%
four-bar burst, rising volume, a volume floor, and an eight-bar extension that
is still under 40%. Horizon is 3 bars. Cap 0.5%. Cost 45 bps.

## L2

Hypothesis: L2 tokens are bets on relative strength versus a benchmark. No
benchmark, or a benchmark in stress, means no trade. Cap 3%. Cost 16 bps.

## RWA

Hypothesis: tokenised real-world assets should be slow. An open-to-prior-close
gap above 8%, or a stress regime, halts the idea. Cap 2%, horizon 24 bars.
Cost 12 bps.

## Perpetual

Hypothesis: negative funding with contained spot drift is a carry observation.
Funding at or above 10 bps with six-bar drift above 4% is a paper short fade,
capped at 1%. Crowded funding without that extension stays an alert. Drift
outside 4% blocks the carry even if funding is negative. Long cap 2%. Cost
10 bps. This does not model liquidation, funding intervals, or exchange risk.

## Book overlay

After the class risk gate, `book.allocate` scales open paper sizes so gross
exposure stays at or under 12% and the crypto-beta cluster (major, large-cap
alt, DeFi, meme, L2) stays at or under 10%. RWA and perpetual buckets stay at
or under 2%. Stablecoin alerts take no budget. The scorecard reports paper
equity by class on the synthetic fixture only.

## Still out of scope

- Live order routing, withdrawal, and trade API keys.
- A broker adapter. That would be a separate human-approved system.
- Claims about future returns. Scores describe the synthetic fixture.

## Version 0.4 information overlays

The class rules above still produce the primary idea. `crypto-intel intel`
then applies three overlays. A failed overlay sets directional paper size to
zero. It does not send an order.

| Class | Confirmation | Size overlay |
|---|---|---|
| Major | Close still above the 8-bar EMA, and not in stress | Vol target 2%, cap 8% |
| Large-cap alt | Breakout volume still at or above its base | Vol target 3%, cap 4% |
| Stablecoin | No directional confirmation. Alerts stay alerts | Cap remains 0 |
| DeFi | Calm realised vol and trend still intact | Vol target 2.5%, cap 2%. `*-LST` sleeve cap 1% |
| Meme | Eight-bar extension still inside 40% | Vol target 5%, cap 0.5% |
| L2 | Benchmark present, not in stress, excess return still positive | Vol target 2.8%, cap 3% |
| RWA | Gap still inside 8% | Vol target 1.5%, cap 2% |
| Perpetual | Funding still supports the carry or the crowded fade | Vol target 2%, long cap 2%, short cap 1% |

Liquid staking is a sleeve inside DeFi, not a ninth class, so the fixture
schema stays stable. Volatility targeting can shrink a size and cannot raise
a class cap.

## Version 0.5 book and pair overlays

The class rules still produce the primary idea. `crypto-intel cross` applies
a book overlay after the v0.4 information path.

| Class | v0.5 enhancement | Effect |
|---|---|---|
| Major | ETH/BTC six-bar relative sleeve, 4% threshold, 2% cap | Names the leader. Stands aside if either leg is in stress. Does not short the laggard |
| Large-cap alt | Beta spillover | Directional size goes to zero when BTC-USD is in stress |
| Stablecoin | Basket contagion | Two or more peg watches become a book alert. Size stays zero |
| DeFi | Beta spillover, including the LST sleeve | Directional size goes to zero in benchmark stress |
| Meme | Beta spillover on top of the chase filter | Directional size goes to zero in benchmark stress |
| L2 | Beta spillover plus the existing benchmark check | Either stress condition blocks the relative-strength idea |
| RWA | Breadth halt only | Not in the crypto-beta cluster. Halted when half of non-stable series are in stress |
| Perpetual | Beta spillover | Carry and crowded-fade paper size go to zero in benchmark stress |

A breadth halt fires when at least half of the non-stable series are in
stress. It overrides every directional idea, including RWA. None of these
overlays can place or route an order.

## Version 0.7 sleeves

`crypto-intel sleeve` is a third pass after the class rule. It can only shrink
paper size. See [v07-automation-and-security.md](v07-automation-and-security.md).

| Class | Sleeve | Effect |
|---|---|---|
| Major | ATR expansion haircut | Last bar range above 2x the prior median halves size |
| Large-cap alt | Relative-lag veto | Missing benchmark, or lagging it by more than 2%, zeroes size |
| Stablecoin | Peg-dispersion watch | Bar range of 40 bps or more is a watch. Size stays zero |
| DeFi | Protocol-gap halt | Open gap above 5% zeroes size |
| Meme | Volume-decay haircut | Volume below half the recent peak halves size |
| L2 | Sequencer-gap proxy | Open gap above 4% zeroes size |
| RWA | Stale-print haircut | Three identical closes halve size |
| Perpetual | Funding-sign flip | A sign change versus the prior bar zeroes carry or fade size |

## Version 0.9 guards

`crypto-intel v09` is a fifth pass. It can only shrink paper size. See
[v09-class-and-cyber.md](v09-class-and-cyber.md).

| Class | Guard | Effect |
|---|---|---|
| Major | Drawdown-cluster haircut | Five consecutive lower closes halve size |
| Large-cap alt | Idiosyncratic gap veto | Open gap above 6% zeroes size |
| Stablecoin | Tertiary peg watch | Deviation of 10 bp or more is a watch. Size stays zero |
| DeFi | Bar-range stress halt | Last bar range above 5% zeroes size |
| Meme | Three-bar chase veto | A 25% rise over three rising bars zeroes size |
| L2 | Benchmark-lag haircut | Lagging the benchmark by more than 4% over six bars halves size |
| RWA | Stale-print veto | More than 36 hours between the last two prints zeroes size |
| Perpetual | Extreme-funding veto | Absolute funding above 20 bp zeroes size |

`crypto-intel alerts` routes information severity only. `crypto-intel zerotrust`
describes the research plane. Neither path can place an order.



