#!/usr/bin/env python3
"""Two-Hour Mean Snapback -- a cbBTC/USDC trading bot for make.fun.

The idea, in one sentence: buy a deep dip below the two-hour mean and ride
the recovery, exiting on a trailing stop.

Why this shape, measured on the competition's frozen dev window (1,440
one-minute bars of cbBTC/USDC, BTC drifting down about 281 bps over the day):
the window is a slow grind, not a trending market. Short-horizon
dip-then-bounce buying loses here (a 45-bar drop keeps falling; bounces are
dead-cat bounces), and every trend-following baseline loses money on it
(EMA-cross -148 USDC, ADX-momentum -76, RSI-Bollinger -40, buy-and-hold -32).
What does work is the long-horizon mean reversion: a close at least 120 bps
below its 120-bar (two-hour) simple moving average reverts toward that mean
over the next hour, and the recovery that follows runs for hours. So the bot
buys the deep dip and then, instead of selling as soon as the price is back
near the mean, it rides the recovery with a trailing stop and a long maximum
hold, so it captures the whole move instead of the first few basis points.

Entry (buy all cash, one position at a time):
  * at least 120 closes of history, so the two-hour mean exists;
  * the close sits at least 120 bps below the 120-bar SMA of closes;
  * the SMA itself is not falling steeply (its 60-bar return is above -60 bps),
    which keeps the bot out of a free-fall;
  * no new entry in the last 120 bars of the window, so a position never has
    to be flattened at the close with no time to recover;
  * a 20-bar cooldown after every exit.

Exit (sell the whole position) on the first of:
  * trailing stop: the close falls 100 bps below the best close since entry;
  * stop-loss: the close falls 100 bps below the entry close;
  * maximum hold: 480 bars (8 hours) have passed since entry.

Every decision is exact integer arithmetic (basis points against integer
micro-USDC prices), so two runs on the same data produce identical orders.
Standard library only. No network, no wall clock, no files outside the repo.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

# --- strategy parameters (scanned on the dev window; see README) ---
SMA_LEN = 120          # two-hour mean, in bars
DIP_BPS = 120          # entry: close this far (bps) below the mean
SLOPE_WIN = 60         # window for the mean's own slope, in bars
SLOPE_MIN_BPS = -60    # entry guard: mean's 60-bar return must beat this
STOP_BPS = 100         # stop-loss vs the entry close
TRAIL_BPS = 100        # trailing stop vs the best close since entry
MAX_HOLD_BARS = 480    # maximum bars to hold a position
COOLDOWN_BARS = 20     # bars to wait after an exit before a new entry
NO_ENTRY_TAIL = 120    # no new entry in the last this many bars
MAX_SLIPPAGE_BPS = 150

# --- state, kept across batches ---
closes = []            # every CBBTC close seen, in order
entry_close = None     # close at the first batch the position was held
best_close = None      # best close since the position opened
held_bars = 0          # bars the current position has been held
cool_until = -1        # bar sequence before which no new entry is allowed


def sma(values, length):
    """Integer mean of the last `length` values."""
    return sum(values[-length:]) // length

def on_batch(state, batch):
    """Decide the orders for one batch. Called once per minute of bars."""
    global entry_close, best_close, held_bars, cool_until
    if state.warming_up:
        return []
    bar = state.latest.get("CBBTC")
    if bar is None:
        return []
    close = int(bar["c"])
    closes.append(close)

    position = state.positions.get("CBBTC")
    if position is not None and position.qty > 0:
        # --- holding: manage the exit ---
        held_bars += 1
        if best_close is None or close > best_close:
            best_close = close
        if entry_close is None:
            entry_close = close
        if len(closes) < SMA_LEN:
            return []
        ret_bps = (close - entry_close) * 10000 // entry_close
        trail_bps = (best_close - close) * 10000 // best_close
        if (trail_bps >= TRAIL_BPS or ret_bps <= -STOP_BPS
                or held_bars >= MAX_HOLD_BARS):
            entry_close = None
            best_close = None
            held_bars = 0
            cool_until = state.seq + COOLDOWN_BARS
            return [{"side": "sell", "symbol": "CBBTC", "qty": position.qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []

    # --- flat: look for the deep-dip entry ---
    entry_close = None
    best_close = None
    held_bars = 0
    if len(closes) < SMA_LEN or state.seq < cool_until:
        return []
    if NO_ENTRY_TAIL and state.seq >= 1440 - NO_ENTRY_TAIL:
        return []
    if state.cash < 1_000_000:
        return []
    mean = sma(closes, SMA_LEN)
    gap_bps = (close - mean) * 10000 // mean
    if len(closes) >= SMA_LEN + SLOPE_WIN:
        old_mean = sma(closes[:-SLOPE_WIN], SMA_LEN)
        slope_bps = (mean - old_mean) * 10000 // old_mean
    else:
        slope_bps = 0
    if gap_bps <= -DIP_BPS and slope_bps > SLOPE_MIN_BPS:
        return [{"side": "buy", "symbol": "CBBTC",
                 "notional_quote_units": state.cash,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


makefun_bars.run(on_batch)
