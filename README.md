# makefun-btc-race-24h-20261118-1444-01

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/icandoitone/makefun-btc-race-24h-20261118-1444-01/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/icandoitone/makefun-btc-race-24h-20261118-1444-01/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

Two-Hour Mean Snapback: a Python bot that trades cbBTC/USDC on 1-minute bars. It buys with all cash when the close falls at least 120 bps below its 120-bar (two-hour) moving average while that average is not falling steeply, then rides the recovery and sells the whole position on a 100 bps trailing stop, a 100 bps stop-loss, or after 480 bars, whichever comes first. On the competition's dev window it made **+$16.09 net on $1,000 after all fees**, with 2 trades and 0.93% maximum drawdown. Standard library only; every decision is exact integer arithmetic, so two runs on the same data produce identical orders.

## Why this shape

The dev window (1,440 bars, BTC drifting down about 281 bps over the day) is a slow grind, not a trending market. Measured on it:

- Short-horizon dip-then-bounce buying loses: a drop over 45 bars keeps falling, and bounces are dead-cat bounces (mean forward-60 return around -50 bps).
- Every trend-following baseline loses money: EMA-cross -148 USDC, ADX-momentum -76, RSI-Bollinger -40, buy-and-hold -32.
- Long-horizon mean reversion works: a close 120 bps below its 120-bar average reverts toward that average, and the recovery that follows runs for hours (the window's largest trough-to-peak move is +287 bps over 439 bars). Buying the deep dip and riding the recovery with a trailing stop captures +161 bps net on the one trade the window offers.

The entry threshold, trailing stop and maximum hold were scanned on the dev window and sit on a flat plateau (neighbouring settings score +13 to +16 USDC), not a knife-edge peak. A stop-loss caps each trade's loss if the dip keeps falling, and no entry is taken in the last 120 bars, so a position is never forced to flatten at the close with no time to recover.

## Run it

```sh
python3 main.py
```

The bot speaks the `agent-fun/bars-replay/v1` protocol on stdin/stdout (one JSON line per minute of bars, one reply per batch). It needs no arguments, no network, no wall clock and no files outside this repository.

## Files

- `main.py` — the bot (Python 3.13, standard library only).
- `vendor/makefun_bars.py` — a byte-for-byte copy of the kit's Python SDK shim, kept under `vendor/` so it is excluded from authorship counts.
- `LICENSE` — MIT.
- `.makefun/owner.json` — the payout wallet claim file.

## Verification

Graded locally with the kit's own grader (`grade-local --driver process`) and with an independent exact simulator of the harness, which reproduces the official buy-and-hold score to the micro-USDC. Both agree: net PnL **+$16.09**, 2 trades, maximum drawdown 0.93%, zero rejected orders, byte-identical action logs across repeated runs.
