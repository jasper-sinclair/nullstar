# Nullstar

<img src="docs/nullstar.png" alt="Nullstar emblem" width="120">

[![Release][release-badge]][release-link]
[![Commits][commits-badge]][commits-link]
[![Downloads][downloads-badge]][downloads-link]
[![License][license-badge]][license-link]

Nullstar is an experimental UCI chess engine by Jasper Sinclair.

The project began in 2026 as a new development line following Jasper's Kobra,
BBCE, and Cobra engines. Nullstar retains that original
chess-engine foundation while developing an independent evaluation, search,
and implementation. OpenAI Codex is used as an engineering and review tool.

The current public release, Nullstar 003, uses a self-contained 768x256 NNUE
evaluator and Jasper Sinclair's Set 006 network. The network is compiled into
the engine, so release executables need no companion files. Version 000 remains
the original strength baseline for controlled testing.

## Repository layout

- `src/`: engine source, Visual Studio project, MinGW Makefile, and embedded
  network source;
- `training/`: NNUE data-processing and training programs;
- `tools/`: development utilities;
- `scripts/`: release-build launchers;
- `docs/`: building, training, network, provenance, and release documentation;
- `binaries/`: ignored local output directory for release executables.

Start with the [`documentation index`](docs/README.md), or see the current
[`release notes`](docs/RELEASE_NOTES.md) directly.

## Building

The supported release matrix provides normal and profile-guided MSVC builds,
plus native and portable AVX2 MinGW builds. Every filename explicitly states
its compiler, CPU target where applicable, and PGO status.

See [`docs/BUILDING.md`](docs/BUILDING.md) for commands and output names.
Official builds use C++23 with MinGW and the latest language mode available in
MSVC.

## License

Copyright (c) 2026 Jasper Sinclair.

Nullstar is distributed under the GNU General Public License version 3 only
(`GPL-3.0-only`). See `LICENSE` and [`docs/PROVENANCE.md`](docs/PROVENANCE.md).

[release-badge]: https://img.shields.io/github/v/release/jasper-sinclair/nullstar?style=for-the-badge&label=official%20release
[release-link]: https://github.com/jasper-sinclair/nullstar/releases/latest
[commits-badge]: https://img.shields.io/github/commits-since/jasper-sinclair/nullstar/latest?style=for-the-badge
[commits-link]: https://github.com/jasper-sinclair/nullstar/commits/main
[downloads-badge]: https://img.shields.io/github/downloads/jasper-sinclair/nullstar/total?style=for-the-badge&color=success
[downloads-link]: https://github.com/jasper-sinclair/nullstar/releases
[license-badge]: https://img.shields.io/github/license/jasper-sinclair/nullstar?style=for-the-badge&label=license&color=success
[license-link]: https://github.com/jasper-sinclair/nullstar/blob/main/LICENSE
