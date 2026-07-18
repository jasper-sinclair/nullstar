# Nullstar

Nullstar is an experimental UCI chess engine by Jasper Sinclair.

The project began in 2026 as a new development line in Jasper's Bitboard Chess,
BBCE, Kobra, and Cobra engine family. Nullstar retains that original
chess-engine foundation while developing an independent evaluation, search,
and implementation. OpenAI Codex is used as an engineering and review tool.

The current `0.1-dev` baseline uses a self-contained 768x256 NNUE evaluator and
an embedded network trained by Jasper Sinclair. It does not contain
`nnue-probe`, the Tulip network, or source code from the Rust Coda engine.
The embedded network predates a correction to the training perspective and is
retained as a transitional, fully owned baseline rather than a release net.

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
