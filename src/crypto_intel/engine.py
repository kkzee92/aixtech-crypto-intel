"""Paper research engine. Live order routing is intentionally absent.

Version 0.3 returns richer backtest diagnostics.
"""

from __future__ import annotations

from statistics import fmean, pstdev

from crypto_intel.costs import round_trip_cost
from crypto_intel.models import Candle, ExecutionMode, PaperFill, Signal
from crypto_intel.regime import atr_pct
from crypto_intel.risk import evaluate
from crypto_intel.security import AuditLog, assert_paper_only
from crypto_intel.strategies import signal_for


def run_once(
    candles: list[Candle],
    *,
    audit: AuditLog,
    kill_switch: bool = False,
    drawdown: float = 0.0,
    benchmark: list[Candle] | None = None,
    mode: ExecutionMode = ExecutionMode.PAPER,
) -> tuple[Signal, PaperFill]:
    assert_paper_only(mode)
    signal = signal_for(candles, benchmark)
    gap = 0.0
    if len(candles) >= 2 and candles[-2].close:
        gap = candles[-1].open / candles[-2].close - 1.0
    recent_atr = atr_pct(candles, 8)
    decision = evaluate(
        signal,
        kill_switch=kill_switch,
        drawdown=drawdown,
        gap_pct=gap,
        recent_atr_pct=recent_atr,
    )
    audit.append("signal", f"{signal.symbol} {signal.side.value} {signal.reason}")
    audit.append("risk", f"allowed={decision.allowed} size={decision.size_fraction:.4f} {'; '.join(decision.reasons)}")
    fill = PaperFill(
        symbol=signal.symbol,
        asset_class=signal.asset_class,
        side=signal.side if decision.allowed else signal.side,
        price=candles[-1].close,
        size_fraction=decision.size_fraction,
        reason=signal.reason if decision.allowed else "; ".join(decision.reasons),
        mode=mode,
        notes=decision.reasons,
    )
    audit.append("paper_fill", f"{fill.symbol} size={fill.size_fraction:.4f} mode={fill.mode.value}")
    return signal, fill


def backtest(candles: list[Candle], *, audit: AuditLog | None = None) -> dict[str, float]:
    """Walk-forward paper backtest. Cost is the declared class assumption.

    Returns equity, trade count, max drawdown, win rate, and a simple Sharpe proxy.
    """
    log = audit or AuditLog()
    equity = 1.0
    peak = 1.0
    trades = 0
    pnls: list[float] = []
    wins = 0
    for index in range(8, len(candles) - 1):
        window = candles[: index + 1]
        drawdown = 1.0 - equity / peak
        _, fill = run_once(window, audit=log, drawdown=drawdown)
        if fill.size_fraction <= 0:
            continue
        forward = candles[index + 1].close / candles[index].close - 1.0
        pnl = fill.size_fraction * (forward - round_trip_cost(fill.asset_class))
        equity *= 1.0 + pnl
        peak = max(peak, equity)
        trades += 1
        pnls.append(pnl)
        if pnl > 0:
            wins += 1
    win_rate = wins / trades if trades else 0.0
    mean_pnl = fmean(pnls) if pnls else 0.0
    std_pnl = pstdev(pnls) if len(pnls) > 1 else 0.0
    sharpe_proxy = mean_pnl / std_pnl if std_pnl else 0.0
    return {
        "ending_equity": round(equity, 6),
        "trades": float(trades),
        "max_drawdown": round(1.0 - equity / peak if peak else 0.0, 6),
        "win_rate": round(win_rate, 4),
        "sharpe_proxy": round(sharpe_proxy, 4),
        "mean_pnl": round(mean_pnl, 6),
    }
