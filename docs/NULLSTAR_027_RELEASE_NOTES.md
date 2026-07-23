# Nullstar 027 release draft

Proposed public version: **Nullstar 027**  
Release date: **TBD**

## GitHub release description

# Nullstar 027

Nullstar 027 is a new public binary release of Nullstar, an experimental
Windows x64 UCI chess engine by Jasper Sinclair.

## Changes

- introduces a new embedded 768x256 side-to-move NNUE network, selected at
  epoch 29 from a completed 30-epoch training run
- aligns quantized NNUE inference with the trainer, including activation
  clipping, scaling, and bias conversion
- corrects edge cases in quiescence terminal detection, static-exchange
  recapture selection, and direct/discovered check detection
- hardens the transposition table with fully guarded 16-byte atomic entries
- expands the reproducible corpus, training, checkpoint-recovery, export,
  parity-checking, build, and test workflows

The network is embedded in every executable; no separate network file is
required.

## Testing

The release candidate completed a 10,240-game gauntlet against a fixed
16-engine strong pool:

- 4,682 wins, 2,326 draws, and 3,232 losses
- 57.08% score
- Ordo rating: 3081 +/- 5.9, with a pool mean of 3020.125
- 640 games against each opponent, split evenly between White and Black
- approximately +59 Ordo Elo and +7.58 percentage points over the immediate
  development predecessor, Nullstar 026, under the same conditions

Conditions were 1.0 second + 0.1 second per move, 32 MB hash, randomized
`book.epd` openings, a 500 cp / 6-move adjudication rule, and a 120-move draw
rule. No illegal-game files or truncated games were found.

All six release-candidate executables passed UCI identification, readiness,
clean termination, depth-5 perft, and deterministic bench checks. Cross-compiler
search results matched at depth 13, the transposition-table concurrency test
passed, and the exported network passed float-versus-quantized parity testing.

## Windows binaries

| Executable | SHA-256 |
|---|---|
| `nullstar_mingw_avx2_nonpgo.exe` | `BC40ED1D7603ADAE174C09A8A93846231F861E0BEC830BF28FBEE0DBD58D8002` |
| `nullstar_mingw_avx2_pgo.exe` | `B7D46D4BD30C560EF12136E78DAD1521F921966DE84A0723890A4186C234E4E9` |
| `nullstar_mingw_native_nonpgo.exe` | `0E9374A9B2F9D1BBEFA5384C2DD884E1785980A82F848CE4EB48967370C6E9D7` |
| `nullstar_mingw_native_pgo.exe` | `4A6968A96881033B4DD4CD0DD989BDEB57D198F8F7024519E6CF1047C139D1A9` |
| `nullstar_msvc_nonpgo.exe` | `76E31DF919BEBD6D55CFD67A1B29771B6E50BC748090BEF53A0B395062A5DDAF` |
| `nullstar_msvc_pgo.exe` | `058BE11693E0A53DCE23C0DAC117D56BE78282E073C4BFCE2FA9A891F6FA53E2` |

For a modern Windows x64 computer, begin with
`nullstar_mingw_avx2_pgo.exe` or `nullstar_msvc_pgo.exe`. The MinGW native
builds are intended for the build computer or a closely compatible processor.

See the repository documentation for complete build, test, network, training,
embedding, provenance, and release information.

Nullstar is released under the GNU General Public License v3.0 only.

---

## Release provenance

The tested primary release executable was:

- executable: `nullstar_mingw_avx2_pgo.exe`
- SHA-256:
  `B7D46D4BD30C560EF12136E78DAD1521F921966DE84A0723890A4186C234E4E9`
- embedded network:
  `network_stm_base_epoch_29.bin`
- network SHA-256:
  `9711CF740BA0C564B62FB41C93CDD0DD9E41FD2960DDC54E8D627C5339A55FCD`
- validation loss: `0.413940`

Verified release executables:

| Executable | Bytes | SHA-256 |
|---|---:|---|
| `nullstar_mingw_avx2_nonpgo.exe` | 1,687,552 | `BC40ED1D7603ADAE174C09A8A93846231F861E0BEC830BF28FBEE0DBD58D8002` |
| `nullstar_mingw_avx2_pgo.exe` | 1,677,312 | `B7D46D4BD30C560EF12136E78DAD1521F921966DE84A0723890A4186C234E4E9` |
| `nullstar_mingw_native_nonpgo.exe` | 1,687,040 | `0E9374A9B2F9D1BBEFA5384C2DD884E1785980A82F848CE4EB48967370C6E9D7` |
| `nullstar_mingw_native_pgo.exe` | 1,676,800 | `4A6968A96881033B4DD4CD0DD989BDEB57D198F8F7024519E6CF1047C139D1A9` |
| `nullstar_msvc_nonpgo.exe` | 859,136 | `76E31DF919BEBD6D55CFD67A1B29771B6E50BC748090BEF53A0B395062A5DDAF` |
| `nullstar_msvc_pgo.exe` | 833,536 | `058BE11693E0A53DCE23C0DAC117D56BE78282E073C4BFCE2FA9A891F6FA53E2` |

## Pre-publication checklist

- [ ] Update release metadata and `docs/RELEASE_NOTES.md` for Nullstar 027.
- [ ] Confirm the release commit contains the exact source used for the verified
      executables.
- [ ] Reconfirm the six executable sizes and SHA-256 values before upload.
- [ ] Confirm that the source archive contains the embedded network provenance
      and all scripts needed for the documented workflow.
- [ ] Create the `nullstar-027` tag on the verified release commit.
- [ ] Attach exactly the six verified executables to the GitHub release.

## Comparison note

The +59 Ordo-Elo comparison is against Nullstar 026 in the same fixed strong
pool and test configuration. It should not be described as a direct measured
gain over public release 003, whose published gauntlet used a different
opponent pool.
