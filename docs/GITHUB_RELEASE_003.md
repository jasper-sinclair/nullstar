# Nullstar 003

Initial public binary release of Nullstar, an experimental Windows x64 UCI chess engine by Jasper Sinclair.

## Changes

* introduces the Set 006 768x256 NNUE network;
* embeds the network directly in each executable;
* includes MSVC and MinGW-w64 PGO and non-PGO builds;
* includes the complete NNUE training and embedding workflow.

## Testing

10,000-game gauntlet against an approximately 2800-rated pool:

* 5099 wins, 1456 draws, 3445 losses
* 58.27%
* estimated rating: 2873

All six binaries passed UCI, readiness, termination, and deterministic benchmark verification.

For most modern Windows systems, begin with `nullstar_mingw_avx2_pgo.exe` or `nullstar_msvc_pgo.exe`. The `native` builds are intended for the build computer or a compatible processor.

See the repository documentation for checksums, build instructions, test conditions, network provenance, and training details.

Licensed under GPL-3.0-only.
