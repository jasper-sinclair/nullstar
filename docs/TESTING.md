# Strength testing

Nullstar development uses high-volume LittleBlitzer gauntlets to detect
playing-strength regressions and to estimate progress against fixed reference
pools. Ratings from these tests apply only to the recorded opponents, time
control, openings, and adjudication settings; they are not universal Elo
claims.

## Current 3020 reference pool

The stronger reference pool contains 16 opponents whose local anchor ratings
sum to 48,322 and average 3020.125.

| Opponent | Anchor rating |
| --- | ---: |
| Vajolet2 2.8.0 | 3097 |
| Strelka 5.5 | 3094 |
| Beef 0.3.6 | 3085 |
| Equinox 3.30 | 3077 |
| Rybka 4.1 | 3068 |
| Atlas 4.35 | 3068 |
| bit-genie-9 | 3059 |
| Protector 1.9.0 | 3049 |
| Combusken 1.3.0 | 3043 |
| Senpai 2.0 | 3027 |
| Protej 0.6.5 | 3016 |
| Monolith 2 | 3002 |
| bobcat-v8.0 | 2998 |
| Pedantic 0.5.0 | 2941 |
| minkochess-1.3 | 2900 |
| pawny-1.2 | 2798 |

The anchor values are retained to reproduce this local pool. Their arithmetic
mean is a calibration reference, not a claim that the values transfer
unchanged to CCRL or another rating list.

## 10,240-game schedule

The current reference schedule uses 10,240 games:

- 16 opponents;
- 640 games per opponent;
- 320 games with Nullstar as White and 320 as Black against every opponent;
- 16 concurrent games.

LittleBlitzer's gauntlet scheduler cycles through all opponents and reverses
the test engine's color after each complete opponent block. Consequently,
every 32 rounds form one complete opponent-and-color cycle, and 10,240 rounds
contain exactly 320 such cycles. See the
[`Tournament.cpp` scheduling code](https://github.com/FireFather/littleblitzer/blob/master/src/Tournament.cpp#L81-L92).

### Opening-selection distinction

The reference configuration uses `Randomize: 1` with the 31,526-position
`book.epd`. LittleBlitzer therefore calls `rand()` separately for every game.
The schedule is exactly balanced by opponent and color, but the reversed-color
game normally receives a different random EPD. The correct description is a
**color-balanced randomized gauntlet**, not a same-position paired gauntlet.
The PGN records the FEN actually used for every game.

With `Randomize: 0`, the unmodified scheduler instead selects one deterministic
EPD for each complete 32-game opponent-and-color cycle. That produces exact
same-position color pairs, but only 320 distinct EPDs in a 10,240-game run.
Changing between these modes changes the methodology and should be recorded
with the result.

## Tournament settings

| Setting | Value |
| --- | --- |
| Tournament | Gauntlet |
| Time control | 1000 ms + 100 ms increment |
| Hash | 32 MB |
| Ponder | Off |
| Own book | Off |
| Starting positions | `book.epd` (31,526 EPDs) |
| Randomize | On |
| Parallel games | 16 |
| Win adjudication | 500 cp for 6 moves |
| Draw adjudication | 120 moves |

## Interpreting the score

Before the final Ordo calculation, the pool mean provides a rough logistic
performance estimate:

| Score | Approximate performance |
| ---: | ---: |
| 50% | 3020 |
| 55% | 3055 |
| 58% | 3076 |
| 60% | 3091 |
| 62% | 3105 |

The final saved report and Ordo result take precedence over this approximation.
Interim results should be treated cautiously even when the schedule is evenly
allocated.

## Build 026 tests

The legacy comparison-pool gauntlet completed on 23 July 2026:

```text
Nullstar 026: 3056 Elo
Games:        10000
Record:       +6987 =1271 -1742
Score:        76.22%
```

The stronger-pool test uses the 3020.125 pool and the 10,240-game schedule
documented above. It began on 23 July 2026 and is currently in progress. Its
result will be added only after all scheduled games and the final report are
complete.
