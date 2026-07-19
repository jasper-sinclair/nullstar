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

Build scripts write these generated executables to the ignored local
`binaries/` directory. Publish release executables as GitHub Release assets;
do not commit them to the source tree.

| Binary | Bytes | SHA-256 |
| --- | ---: | --- |
| `nullstar_msvc_nonpgo.exe` | 858,624 | `A8EDEC9A3615CCDABA69343BE1B04D5B502EF763AEAFCA93DD6234B3EF6B3E51` |
| `nullstar_msvc_pgo.exe` | 834,560 | `9CE82AE8B8F6141B6C01E3328A18C9C287D671BE9C6E6FB4D3F8FB0F281F141E` |
| `nullstar_mingw_native_nonpgo.exe` | 1,686,528 | `58B3BDBDD4CAE90561FD71CF9C0772314DA21B28E00E339281BC8CC3DB79A07E` |
| `nullstar_mingw_native_pgo.exe` | 1,679,872 | `B2F3F621B23381609E855002F092CC59725F3A915B9FD6E37C4395FFCAF83858` |
| `nullstar_mingw_avx2_nonpgo.exe` | 1,687,552 | `E949931570ABA0BC6F12F6F8F226421062A00F762E5530EC9DC4486281A541F7` |
| `nullstar_mingw_avx2_pgo.exe` | 1,680,384 | `BF69AEC2860B1BA0330A5185A17E5DA4053ADB56133A86AF1644528772F0E7E1` |

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
