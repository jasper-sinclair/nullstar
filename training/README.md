# Nullstar NNUE training

Nullstar's evaluator consumes two shared-feature accumulators in this order:

1. side to move;
2. opponent.

Engine self-play writes labels from the side-to-move perspective. The converter
therefore orders white/black feature sets according to the FEN side-to-move
field and leaves those labels unchanged. For datasets whose results are from
White's perspective, set `label_perspective` to `white`; black-to-move targets
will then be inverted during conversion.

Run `run_pipeline.bat` from this directory after placing `training.txt` here.
Configuration is stored in `config.json`. Generated datasets, checkpoints,
networks, and logs are intentionally excluded from Git.

The 768x256 network embedded in the initial Nullstar baseline predates this
perspective correction. It is retained only as an owned transitional baseline;
a newly trained network should replace it before a strength release.
