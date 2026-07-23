# Nullstar 027 release notes

Released: 23 July 2026

Nullstar 027 is the second public binary release of Nullstar, an experimental
Windows x64 UCI chess engine by Jasper Sinclair. It introduces a new
side-to-move NNUE network, corrects quantized inference and several search
edge cases, and expands the reproducible development and verification
workflow.

## Strength test

Nullstar 027 completed a 10,240-game gauntlet against a fixed 16-engine strong
pool averaging 3020.125:

```text
Rating: 3081 (Ordo error 5.9)
Wins:   4682
Draws:  2326
Losses: 3232
Score:  57.08%
```

Test conditions:

- 32 MB hash;
- 1000 ms base time plus 100 ms increment;
- 16 concurrent games;
- adjudication at 500 centipawns for six moves;
- draw adjudication at 120 moves;
- randomized 31,526-position `book.epd`;
- exactly 640 games per opponent, with 320 games as each color.

The PGN contained all 10,240 games, with no truncated games or illegal-move
dump files. Ratings from this fixed local pool and time control are not
universal Elo claims.

Under the same conditions, Nullstar 026 scored 49.50% and received an Ordo
rating of 3022. Nullstar 027 gained 59 Ordo Elo and 7.58 score percentage
points. This is not a direct comparison with public release 003, whose
published gauntlet used a different opponent pool.

## Changes from Nullstar 003

- replaces Set 006 with Jasper Sinclair's 768x256 `stm-base` epoch 29
  side-to-move NNUE network;
- aligns the quantized evaluator with the trainer's activation clipping,
  scaling, and bias conversion;
- corrects quiescence terminal detection when the transposition-table move is
  the only legal move;
- restricts static-exchange recapture selection to attackers of the side to
  move;
- evaluates direct and discovered checks using complete post-move occupancy;
- packs transposition-table entries into fully guarded 16-byte atomic slots;
- adds corpus manifests, perspective validation, safe checkpoint recovery,
  and float-versus-quantized export-parity verification;
- expands automated release verification across all six MSVC and MinGW-w64
  PGO and non-PGO binaries.

## NNUE network

The network was selected at epoch 29 from a completed 30-epoch training run
with a validation loss of `0.413940`. It is embedded in every executable; no
separate network file is required.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Quantized `network_stm_base_epoch_29.bin` | 394,754 | `9711CF740BA0C564B62FB41C93CDD0DD9E41FD2960DDC54E8D627C5339A55FCD` |
| Generated `src/net.cpp` | 2,492,329 | `E323DC98EE0C33F41C324279CB6D4AE58146BF0BC8DD1AE2D6A3ED57B6DF541C` |

## Windows binaries

Build scripts write these generated executables to the ignored local
`binaries/` directory. Publish release executables as GitHub Release assets;
do not commit them to the source tree.

| Binary | Bytes | SHA-256 |
| --- | ---: | --- |
| `nullstar_msvc_nonpgo.exe` | 859,136 | `76E31DF919BEBD6D55CFD67A1B29771B6E50BC748090BEF53A0B395062A5DDAF` |
| `nullstar_msvc_pgo.exe` | 833,536 | `058BE11693E0A53DCE23C0DAC117D56BE78282E073C4BFCE2FA9A891F6FA53E2` |
| `nullstar_mingw_native_nonpgo.exe` | 1,687,040 | `0E9374A9B2F9D1BBEFA5384C2DD884E1785980A82F848CE4EB48967370C6E9D7` |
| `nullstar_mingw_native_pgo.exe` | 1,676,800 | `4A6968A96881033B4DD4CD0DD989BDEB57D198F8F7024519E6CF1047C139D1A9` |
| `nullstar_mingw_avx2_nonpgo.exe` | 1,687,552 | `BC40ED1D7603ADAE174C09A8A93846231F861E0BEC830BF28FBEE0DBD58D8002` |
| `nullstar_mingw_avx2_pgo.exe` | 1,677,312 | `B7D46D4BD30C560EF12136E78DAD1521F921966DE84A0723890A4186C234E4E9` |

The MinGW `native` binaries are tuned for the build computer and should be
used only on that computer or a demonstrably compatible processor. The MinGW
`avx2` binaries target x86-64-v3, which includes AVX2, BMI2, and related
instructions. The MSVC release configuration also requires AVX2.

All six binaries passed UCI identification, readiness, normal termination,
the 4,865,609-node depth-5 start-position perft, and the 801,905-node
deterministic depth-10 benchmark. Cross-compiler search results also matched
at depth 13. The transposition-table concurrency probe and NNUE export-parity
test passed.

## Source and license

Nullstar is distributed under `GPL-3.0-only`. The repository contains the
engine source, embedded network source, training tools, embedding utility,
build instructions, test methodology, and provenance documentation. Generated
datasets, checkpoints, local Python environments, build objects, and
executables are not stored in source control.

The concise GitHub release description is
[`GITHUB_RELEASE_027.md`](GITHUB_RELEASE_027.md).
