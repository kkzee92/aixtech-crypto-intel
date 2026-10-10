# Asset-class strategy notes — Enhanced v0.24

These rules are research heuristics for a paper-only information system. Each class has an edge hypothesis, an entry, an invalidation, a horizon, a size cap, and now multi-factor confirmation overlays that can only shrink paper size. They are not a promise of return. No live execution.

## Shared enhancements (v0.24)

- Adaptive regime filter: volatility-adjusted EMA spans and ATR-normalized thresholds.
- Multi-factor confirmation: volume, momentum (RSI/MACD-style), and relative strength must align before directional size is considered.
- All new overlays and guards can only shrink or zero paper size; they cannot raise class caps or enable live trading.
- Synthetic fixtures only. Scores describe the fixture, not future returns.

Regime labels remain: trend, range, stress (from regime.py).

## Major (BTC, ETH)

Hypothesis: Liquid majors exhibit persistent trends and mean-reverting ranges, but require multi-factor confirmation to filter noise.

Entry:
- Trend: Adaptive fast EMA (span 5–8 based on ATR) above slow EMA (span 13–21), RSI 40–65, MACD histogram positive, volume > 1.1× 20-bar average, non-stress regime.
- Range mean-reversion: RSI < 28 and rising, close above prior bar, volume confirmation, range regime only.

Invalidation: Stress regime, RSI > 72 on trend entry, or volume divergence (price up, volume down 3 bars).

Horizon: 12–24 bars. Cap 8%. Cost 8 bps. Vol-target overlay can shrink further.

## Large-cap alt

Hypothesis: Breakouts succeed only with sustained volume and relative strength versus BTC.

Entry: Close above prior 5-bar high, volume ≥ 1.3× average, relative strength vs BTC > 1.5% over 6 bars, non-stress, and not lagging BTC by > 2%.

Invalidation: Stress, volume < base, or relative lag > 3%.

Cap 4%. Cost 14 bps.

## Stablecoin

Hypothesis: Peg integrity is the sole signal. Multi-threshold monitoring with velocity.

Entry: None. Alerts only.
- Watch: |deviation| ≥ 15 bps or velocity ≥ 10 bps in one bar.
- Depeg alert: |deviation| ≥ 40 bps or persistent (3 bars) ≥ 20 bps.

Size always 0. Cost n/a.

## DeFi

Hypothesis: Protocol tokens trend in low-volatility, non-stress regimes with liquidity confirmation.

Entry: Close > 8-bar adaptive EMA, realized vol (8-bar MAD) ≤ 5%, volume > median, non-stress, gap < 3%.

Invalidation: Stress, realized vol > 6%, or open gap > 4%.

Cap 2%. LST sleeve sub-cap 1%. Cost 22 bps.

## Meme

Hypothesis: Extreme bursts can be captured with strict time stops and anti-chase filters; most are untradeable.

Entry: 4-bar burst ≥ 12% with rising volume, 8-bar extension < 35%, volume floor met, non-stress, and not already extended on prior bars.

Invalidation: Extension > 40%, volume decay, wick rejection, or liquidity proxy thin.

Horizon: 3 bars hard stop. Cap 0.5%. Cost 45 bps.

## L2

Hypothesis: Relative strength versus ETH or BTC benchmark, adjusted for sequencer/fee proxies.

Entry: 6-bar excess return ≥ 2.5% vs non-stress benchmark, volume confirmation, fee/volume spike not extreme.

Invalidation: Missing or stressed benchmark, lag > 3%, or fee-spike proxy.

Cap 3%. Cost 16 bps.

## RWA

Hypothesis: Tokenized assets move slowly; gaps and staleness are hard halts.

Entry: Close > 8-bar EMA and > close 5 bars ago, gap < 6%, non-stress, no stale prints (identical closes).

Invalidation: Gap > 8%, stress, or stale NAV proxy.

Horizon: 24 bars. Cap 2%. Cost 12 bps.

## Perpetual

Hypothesis: Negative funding with contained drift is a carry observation; extreme positive funding with extension can be a paper fade.

Entry (carry): Funding ≤ -4 bps, |6-bar drift| < 3.5%, non-stress.
Entry (fade): Funding ≥ 12 bps and 6-bar drift > 4% (paper short, cap 1%).

Invalidation: Funding sign flip, extreme funding (|f| > 25 bps), or drift expansion.

Long cap 2%, short cap 1%. Cost 10 bps. Does not model liquidations.

## Book and multi-pass overlays

After class rules and risk gate:
- Book gross ≤ 12%, crypto-beta cluster ≤ 10%.
- All v0.4–v0.23 overlays and the new v0.24 multi-factor guards can only shrink size.
- New v0.24 multi-factor confirmation must pass before any directional size is retained.

## Still out of scope

- Live order routing, trade/withdrawal keys, broker adapters.
- Claims of future returns or investment advice.
- Any path that can enable live execution.
