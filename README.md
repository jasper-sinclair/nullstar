# Nullstar

Nullstar is an experimental UCI chess engine by Jasper Sinclair.

The project began in 2026 as a new development line following Jasper's Kobra,
BBCE, and Cobra engines. Nullstar retains that original
chess-engine foundation while developing an independent evaluation, search,
and implementation. OpenAI Codex is used as an engineering and review tool.

The current `003` development version uses a self-contained 768x256 NNUE
evaluator and Jasper Sinclair's Set 006 network. The network is compiled into
the engine, so release executables need no companion files. Version 000 remains
the original strength baseline for controlled testing.

## Repository layout

- `src/`: engine source, Visual Studio project, MinGW Makefile, and embedded
  network source;
- `training/`: self-play data conversion, validation, training, export, and
  visualization tools;
- `tools/embed_file/`: portable C++ utility that converts `network.bin` into
  the tracked `src/net.cpp` array.

See [`NETWORK.md`](NETWORK.md) for the active network's hashes and provenance,
and [`training/README.md`](training/README.md) for the complete self-play to
engine workflow. See [`RELEASE_NOTES.md`](RELEASE_NOTES.md) for the current
release result, binary checksums, and compatibility requirements.

## Building

The supported release matrix provides normal and profile-guided MSVC builds,
plus native and portable AVX2 MinGW builds. Every filename explicitly states
its compiler, CPU target where applicable, and PGO status.

See [`BUILDING.md`](BUILDING.md) for commands and output names. Official builds
use C++23 with MinGW and the latest language mode available in MSVC.

## License

Copyright (c) 2026 Jasper Sinclair.

Nullstar is distributed under the GNU General Public License version 3 only
(`GPL-3.0-only`). See `LICENSE` and `PROVENANCE.md`.
