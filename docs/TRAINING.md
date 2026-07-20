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

A combined text corpus must never mix these conventions. Build a canonical
side-to-move corpus with `build_master_corpus.py`; each source declares its
own input perspective and the tool validates every record, converts only the
required black-to-move labels, and writes a SHA-256 manifest. For example:

```powershell
python build_master_corpus.py `
  --source .\old_training.txt white `
  --source .\new_selfplay.txt side_to_move `
  --output .\training_master_stm.txt `
  --target-perspective side_to_move
```

The command refuses to overwrite a source or an existing output. Retain the
original source files and use the generated manifest as the perspective and
provenance record. Future native Nullstar self-play may be added as another
`side_to_move` source when building the next master corpus.
If an interrupted conversion leaves `OUTPUT.part`, inspect it and use
`--replace-incomplete` to restart; that option never replaces a completed
master corpus.

`verify_perspective_conversion.py` can independently compare the source and
finished master record by record, including every FEN and transformed label.

Set `corpus_manifest` to that manifest in `config.json` and enable
`require_corpus_manifest` for a master corpus. The pipeline then refuses to
continue when its path, byte size, or label perspective disagrees with the
manifest. `verify_corpus_sha256` enables a slower full-file hash check.

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

On Jasper's development layout, the CPU launchers in `scripts/` activate the
established environment and run the corresponding configuration:

```text
train_full_cpu.bat       full corpus, 20 epochs
train_existing_full_cpu.bat
                         train/resume from verified full sparse data
train_existing_smoke_1m_cpu.bat
                         trainer-only smoke test using verified sparse data
train_smoke_1m_cpu.bat   first 1,000,000 records, 1 epoch, no text shuffle
```

The smoke profile is `training/configs/smoke-1m.json`. It writes every sparse,
checkpoint, log, model, and network artifact beneath `training/smoke/`, so it
cannot resume or overwrite the full experiment. `run_pipeline.py` accepts an
optional configuration path and passes it consistently to every stage:

```powershell
python run_pipeline.py configs\smoke-1m.json
```

The pipeline validates the text data, shuffles it, converts it to
`training_sparse.bin`, validates both the binary structure and sparse feature
orientation, and runs `train.py`. A shuffled corpus is fully validated again
before conversion. Shuffled and sparse outputs are written to `.part` files
and replace their final paths only after successful completion. Perspective
meaning cannot be inferred from FEN and label values alone, so
`label_perspective` must agree with the source corpus or its generated
manifest. `check_selfplay_perspective_features.py` is only applicable to
unmodified native Nullstar self-play and may be run independently.

`verification_scan_limit` and `structure_verify_limit` bound the independent
sparse-data audits without limiting the dataset used by `train.py`. Set either
limit to zero for a full scan. Text validation remains streaming and does not
retain per-position statistics in memory.

The current full STM profile writes:

- `best_model_stm_base.pt`: best floating-point PyTorch state;
- `checkpoint_stm_base.pt`: resumable model, optimizer, and scheduler state;
- `checkpoint_mid_epoch_stm_base.pt`: latest configured mid-epoch recovery state;
- `network_stm_base.bin`: best quantized network for the engine;
- `network_stm_base_epoch_*.bin`: optional per-epoch exports;
- `training_stm_base.log`: progress and validation losses.
- `training_stm_base_pipeline.log`: persistent validation, shuffling,
  conversion, verification, and training console output.

The trainer resumes automatically when its configured checkpoint exists. Move
or clean that checkpoint before intentionally starting a fresh experiment.
For datasets too large for Python index lists, the trainer builds and reuses a
disk-backed `uint64` record-offset index. Its block sampler changes training
order each epoch without allocating a full-record permutation. Use
`train_existing_full_cpu.bat` after a training-only failure when the atomic
full sparse file has already passed pipeline verification.

`clean_here.bat` provides separately confirmed cleanup modes for legacy Set
006 artifacts, the current full STM training state, the isolated smoke test,
and the expensive full shuffled/sparse data. It anchors itself to the training
directory and never uses a broad `*.pt` deletion.

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
Its explicit `white` label perspective describes the historical normalized
text corpus; use the active side-to-move configuration with the new canonical
master instead.
The active `config.json` includes the corrected, explicit label-perspective
handling and is the recommended starting point for new experiments.
