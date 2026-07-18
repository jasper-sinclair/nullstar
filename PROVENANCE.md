# Provenance

Nullstar belongs to Jasper Sinclair's original chess-engine lineage:
Bitboard Chess, BBCE, Kobra, Cobra, and now Nullstar. A public GPLv3 snapshot
of BBCE is available at [jasper-sinclair/bbce](https://github.com/jasper-sinclair/bbce);
the preserved local public snapshot is commit
`3b4b6492287f281ad4b28bd66f0ef570407a056e`. Core board, attack, move
generation, hashing, move ordering, search, and UCI modules evolved through
that line, while later engines replaced and extended substantial components.

The direct Nullstar import was made in 2026 from the Cobra 1.0 public source at
commit `79af924eddb41b1c8c24fe47a29bcd22e1701b58`.

Jasper Sinclair is the author and copyright holder of the imported chess board,
move generation, search, UCI, self-play, training, and compact NNUE inference
code, subject to the history and notices in the BBCE, Kobra, and Cobra
repositories. The imported code remains licensed under GPLv3. Nullstar is
distributed under `GPL-3.0-only`.

The initial embedded 768x256 network was trained by Jasper Sinclair with his
Cobra training pipeline. Its original binary has SHA-256:

`222894CA3D30091AA391365B06E4A1D07E69274CDD8CD3A308AD6CA02926CDEE`
