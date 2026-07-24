# Nullstar 027

Second public binary release of Nullstar, an experimental Windows x64 UCI chess engine by Jasper Sinclair.

## Changes

* introduces a new 768x256 side-to-move NNUE network;
* embeds the network directly in each executable;
* aligns quantized NNUE inference with the trainer;
* includes search-correctness improvements and a hardened transposition table;
* includes MSVC and MinGW-w64 PGO and non-PGO builds;
* expands the reproducible NNUE training, export, and parity-verification workflow.

## Testing

10,240-game gauntlet against a fixed 16-engine pool averaging 3020:

* 4682 wins, 2326 draws, 3232 losses
* 57.08%
* Ordo rating: 3081 (error: 5.9)
* 59 Ordo Elo above Nullstar 026 under the same conditions

All six binaries passed UCI, readiness, termination, perft, and deterministic benchmark verification. Cross-compiler search results also matched.

For most modern Windows systems, begin with `nullstar_mingw_avx2_pgo.exe` or `nullstar_msvc_pgo.exe`. The distributed MinGW `native` builds were compiled on an Intel Core i9-13900K and are intended for that processor or CPUs supporting an equivalent or greater instruction set.

See the repository documentation for checksums, build instructions, test conditions, network provenance, and training details.

Licensed under GPL-3.0-only.
