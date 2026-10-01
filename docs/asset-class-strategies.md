# Asset-class strategy notes

These rules are research heuristics. They exist so each asset class has an
explicit edge hypothesis, a failure mode, and a size cap. They are not a
promise of return.

## Major

Hypothesis: liquid majors trend often enough that a fast EMA above a slow EMA
is usable, unless RSI is already stretched. A second path looks for washed-out
RSI that has stopped falling. Cap 8%, horizon 8 or 20 bars.

## Large-cap alt

Hypothesis: breakouts without volume are noise. The rule needs a close above
the prior five-bar high and volume at least 1.2 times the recent average.
Cap 4%.

## Stablecoin

Hypothesis: the useful signal is a peg break, not direction. Deviation of 50
bps or more raises an alert. Risk gate forces size to zero.

## DeFi

Hypothesis: trend signals in high realised-volatility regimes are mostly gap
risk. If mean absolute return over 8 bars exceeds 6%, stand aside. Cap 2%.

## Meme

Hypothesis: most bursts are untradeable because proxy liquidity is thin. A
long is allowed only after a 15% four-bar burst, rising volume, and a volume
floor. Horizon is 3 bars and the cap is 0.5%.

## L2

Hypothesis: L2 tokens are bets on relative strength versus a benchmark
(ETH in the fixture). No benchmark means no trade. Cap 3%.

## RWA

Hypothesis: tokenised real-world assets should be slow. An open-to-prior-close
gap above 8% halts the idea. Cap 2%, horizon 24 bars.

## Perpetual

Hypothesis: negative funding with contained spot drift is a carry observation,
not a directional forecast. Funding at or above 10 bps blocks the long carry.
Cap 2%. This does not model liquidation, funding intervals, or exchange risk.

## Enhancement backlog

- Regime filter shared across classes, still paper-only.
- Cost model by asset class (spread, funding, slippage) using declared assumptions.
- Read-only public market adapter behind the existing injected fetcher.
- Human approval token before any future broker adapter, in a separate repository.
