# Nullstar 003 release notes

Released: 19 July 2026

Nullstar 003 is an experimental Windows x64 UCI chess-engine release by Jasper
Sinclair. It introduces the Set 006 768x256 NNUE network and makes the complete
network-development workflow part of the source repository.

## Strength test

Nullstar 003 completed a 10,000-game gauntlet against an approximately
2800-rated engine pool:

```text
Rating: 2873
Wins:   5099
Draws:  1456
Losses: 3445
Score:  58.27%
```

Test conditions:

- 32 MB hash;
- 1000 ms base time plus 100 ms increment;
- adjudication at 500 centipawns for six moves;
- draw adjudication at 120 moves;
- 31,526-position `book.epd`, with paired colors.

The rating is specific to this test pool and time control; it is not intended
as a universal rating claim. The result reproduces the strength of the private
Nullstar 002 validation candidate, which scored 58.53% in the corresponding
10,000-game gauntlet. Versions 002 and 003 contain identical quantized network
bytes. Version 003 adds the reproducible generated representation and complete
development infrastructure.

## Changes from Nullstar 000

- replaces the transitional baseline network with Jasper Sinclair's Set 006
  768x256 NNUE network;
- embeds the network in the executable, with no external runtime file;
- includes the full self-play, validation, sparse conversion, training,
  visualization, and quantized-export pipeline;
- includes the portable C++ `embed_file` source and CMake project;
- documents network hashes, training configuration, provenance, and the
  complete source-to-release workflow;
- provides freshly trained PGO and non-PGO builds for MSVC and MinGW;
- updates the deterministic PGO regression signature for Set 006;
- identifies all standard release binaries as `Nullstar 003`.

There is no intentional search-algorithm change between the tested Nullstar
002 candidate and Nullstar 003.

## Windows binaries

| Binary | Bytes | SHA-256 |
| --- | ---: | --- |
| `nullstar_msvc_nonpgo.exe` | 858,624 | `3D53A429F610F865BD2897D4E21AAFF731568F5A7A3A175E5F268B5D22C30C4B` |
| `nullstar_msvc_pgo.exe` | 834,560 | `B09DC09691E5E01ED09BDF375307AE8DE7DC3A78454AE197EE01B36A68112814` |
| `nullstar_mingw_native_nonpgo.exe` | 1,686,528 | `1B7F0ECB9AD8A703E702CE02AEF902A296C5F3256A7228037162D2982F9C4955` |
| `nullstar_mingw_native_pgo.exe` | 1,679,872 | `8237C98DCE6CD60CF28DA8784FE1FA25B81B7B3FB898AE38D191ED1B6D8C354B` |
| `nullstar_mingw_avx2_nonpgo.exe` | 1,687,552 | `6F6D690B994B430282E99A5C933F373C045F46C0250EB781A5112CF9FDC03B4C` |
| `nullstar_mingw_avx2_pgo.exe` | 1,680,384 | `21B2C3794EA4397E282022485F32BC56DEB34C3B08FC3E865110AA90314984A0` |

The MinGW `native` binaries are tuned for the build computer and should be
used only on that computer or a demonstrably compatible processor. The MinGW
`avx2` binaries target x86-64-v3, which includes AVX2, BMI2, and related
instructions. The MSVC release configuration also requires AVX2.

Every binary passed UCI initialization, readiness, normal termination, and the
deterministic 32-position depth-10 benchmark of 890,981 nodes.

## Source and license

Nullstar is distributed under `GPL-3.0-only`. The repository contains the
engine source, embedded network source, training tools, embedding utility,
build instructions, and provenance documentation. Generated datasets,
checkpoints, local Python environments, build objects, and executables are not
stored in source control.
