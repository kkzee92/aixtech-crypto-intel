# Version 0.8 enhancements: robustness, multi-window confirmation, and expanded cyber controls

Research update for the paper-only crypto trading information system. Builds on v0.7 multi-factor (EMA, MACD-style, Bollinger-style, trend strength, vol scaling) with median-based volume for outlier resistance, stricter multi-window EMA slope confirmation, multi-print funding stability, and expanded secret redaction. Not financial advice; scores describe synthetic fixtures only.

## Strategy enhancements (per asset class)

- **Major**: Added short-window EMA slope confirmation in addition to multi-EMA + MACD + BB + strength. Adaptive RSI retained.
- **Large-cap alt**: Volume confirmation now uses median of recent volumes (more robust to spikes) plus prior factors.
- **Stablecoin**: Depeg alert prefers sustained multi-bar elevation.
- **DeFi**: Volume support now versus median.
- **Meme**: Liquidity floor and volume checks use median; prior filters retained.
- **L2**: Relative volume uses medians for both own and benchmark series.
- **RWA**: Unchanged core with prior momentum/strength.
- **Perpetual**: Funding stability checked across recent prints (not single bar).

All sizes remain volatility-scaled. Regime overlay and stress stand-aside unchanged. Paper-only preserved. No live paths.

## Security and data architecture enhancements

- Expanded SECRET_PATTERNS with GitHub PAT style (`ghp_`), PEM private-key headers, and additional token formats.
- Added `anomaly_score` helper (max absolute return + volume spike vs median) for research logging of series integrity.
- Reinforced zero-trust notes in sanitization: independent re-evaluation, no assumed clean state.
- Series integrity remains SHA-256. Continued PDPA tripwire, gitleaks, paper-only mode, no live keys, RBAC with no trader role.
- Data classification notes updated for additional secret types.

These remain research heuristics. A production system would require separate human-approved broker integration, formal threat modeling, compliance review, real market data (never in this repo), and independent security assessment.

See updated `src/crypto_intel/strategies.py` and `src/crypto_intel/security.py`. This version is 0.8.0.
