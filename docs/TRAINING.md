# Nullstar NNUE training

The `training/` directory contains the complete source pipeline used to prepare
data, train, validate, visualize, and export Nullstar's compact NNUE networks.
Large datasets, Python environments, checkpoints, and generated networks are
build artifacts and are intentionally not stored in Git.

## Network and data layout

Nullstar uses 768 piece-square input features and a shared 256-neuron hidden
layer. Two accumulators are presented to the output layer in this order:

1. side to move;
2. opponent.

Engine self-play writes `FEN | result` records whose result is from the side
to move's perspective. Keep `label_perspective` set to `side_to_move` for this
data. For an imported dataset labelled from White's perspective, set it to
`white`; the converter will invert black-to-move labels.

The sparse training record is:

```text
uint8   side-to-move feature count
uint8   opponent feature count
uint16  side-to-move feature indices[]
uint16  opponent feature indices[]
float32 result
```

## 1. Create the Python environment

From the repository root, enter the training directory and create the
environment:

```powershell
Set-Location .\training
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

PyTorch publishes different CPU and CUDA packages. For GPU training, install
the appropriate PyTorch build for the machine before installing the remaining
requirements. The trainer's `device` setting may be `auto`, `cpu`, or `cuda`.

## 2. Generate self-play data

First build Nullstar. Start the engine with this directory as its current
working directory so it creates `training.txt` here:

```powershell
Set-Location .\training
..\binaries\nullstar_mingw_avx2_pgo.exe
```

At the engine prompt, for example:

```text
selfplay 5000000 nodes 8000 threads 8
quit
```

Self-play appends to an existing `training.txt`; move or delete an old dataset
before starting an unrelated run. Smaller commands such as `selfplay 20
movetime 50` are useful for checking the pipeline.

## 3. Configure and train

Edit `config.json`, then run:

```powershell
python run_pipeline.py
```

The pipeline checks the self-play perspective, shuffles the text data,
converts it to `training_sparse.bin`, validates the binary structure, and runs
`train.py`. `verify_training_txt.py` and `verify_sparse_features.py` provide
additional audits and can be run independently before a long training job.

Important outputs are:

- `best_model.pt`: best floating-point PyTorch state;
- `checkpoint.pt`: resumable model, optimizer, and scheduler state;
- `network.bin`: best quantized network for the engine;
- `network_epoch_*.bin`: optional per-epoch exports;
- `training.log`: progress and validation losses.

The trainer resumes automatically when `checkpoint.pt` exists. Move previous
checkpoints before intentionally starting a fresh experiment.

## 4. Embed the network

From the repository root, build the utility documented in
[`EMBEDDING.md`](EMBEDDING.md), then run:

```powershell
.\build\tools\embed_file.exe .\training\network.bin .\src\net.cpp
```

Rebuild Nullstar and verify its UCI initialization and benchmark before match
testing. The generated `src/net.cpp` is the canonical network included in the
source tree; the finished executable needs no external `network.bin`.

## Historical configuration

`configs/nullstar-002-set006.json` preserves the archived hyperparameters for
the Set 006 network introduced in Nullstar 002 and retained in Nullstar 003.
The active `config.json` includes the corrected, explicit label-perspective
handling and is the recommended starting point for new experiments.
