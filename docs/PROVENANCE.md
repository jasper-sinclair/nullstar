# Provenance

Nullstar belongs to Jasper Sinclair's original chess-engine lineage: Kobra,
BBCE, Cobra, and now Nullstar. A public GPLv3 snapshot
of BBCE is available at [jasper-sinclair/bbce](https://github.com/jasper-sinclair/bbce);
the preserved local public snapshot is commit
`3b4b6492287f281ad4b28bd66f0ef570407a056e`. Core board, attack, move
generation, hashing, move ordering, search, and UCI modules evolved through
that line, while later engines replaced and extended substantial components.

The direct Nullstar import was made in 2026 from the Cobra 1.0 public source at
commit `79af924eddb41b1c8c24fe47a29bcd22e1701b58`.

## NNUE implementation history

Kobra's public documentation credits a highly optimized custom adaptation of
Daniel Shawul's [`nnue-probe`](https://github.com/dshawul/nnue-probe). That
acknowledgment remains part of Kobra's implementation history.

Nullstar does not use, include, link to, or require `nnue-probe`. Its current
compact NNUE inference implementation is maintained directly in `src/nnue.cpp`
and `src/nnue.h`, with quantized network parameters embedded through
`src/net.cpp`. The earlier Kobra acknowledgment therefore describes Kobra; it
is not a Nullstar source or runtime dependency.

Jasper Sinclair is the author and copyright holder of the imported chess board,
move generation, search, UCI, self-play, training, and compact NNUE inference
code, subject to the history and notices in the Kobra, BBCE, and Cobra
repositories. The imported code remains licensed under GPLv3. Nullstar is
distributed under `GPL-3.0-only`.

The NNUE training and validation scripts in `training/` evolved from Jasper
Sinclair's `kobra-train` repository and were adapted for Nullstar's explicit
side-to-move feature and label order. The `tools/embed_file` utility is also
Jasper Sinclair's development code. Both are distributed here under the same
`GPL-3.0-only` license as Nullstar.

The initial Nullstar 000 embedded 768x256 network was trained by Jasper
Sinclair with his Cobra training pipeline. Its original binary has SHA-256:

`222894CA3D30091AA391365B06E4A1D07E69274CDD8CD3A308AD6CA02926CDEE`

Nullstar 002 introduced Jasper Sinclair's later 768x256 Set 006 network, and
Nullstar 003 retains the same quantized network in a cleanly regenerated C++
representation. Its quantized binary has SHA-256:

`30A74951A897E696A5156BC9E192771DB99FE5754A6431D7EA2D562003224CE6`

See [`NETWORK.md`](NETWORK.md) for artifact hashes, archived configuration
details, and the reproduction boundary for the original multi-gigabyte
training dataset.
