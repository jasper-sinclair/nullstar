# train.py
# jasper sinclair
#
# Trains a simple NNUE-style chess evaluation network using sparse binary data.
# Exports quantized weights for use inside a chess engine.

import torch
import torch.nn as nn
import torch.optim as optim

# Improve CUDA performance
torch.backends.cudnn.benchmark = True
torch.set_float32_matmul_precision('high')

from torch.utils.data import DataLoader, Dataset, Sampler
from array import array
import numpy as np
import struct
import mmap
import json
import os
import sys
import random
import time
import logging


# =========================
# Logging Setup
# =========================
# Logs to both file and stdout for persistent training history.

logger = logging.getLogger("nullstar-training")
logger.setLevel(logging.INFO)


def configure_logging(path):
    logger.handlers.clear()
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)

    file_handler = logging.FileHandler(path, delay=False)
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


# =========================
# Constants
# =========================

# 6 piece types × 64 squares × 2 colors (us/them)
INPUT_SIZE = 768

WHITE = 0
BLACK = 1

# Piece type mapping (color handled separately)
PIECE_TO_INDEX = {
    "P": 0,
    "N": 1,
    "B": 2,
    "R": 3,
    "Q": 4,
    "K": 5,
    "p": 0,
    "n": 1,
    "b": 2,
    "r": 3,
    "q": 4,
    "k": 5,
}

OFFSET_INDEX_KIND = "nullstar-sparse-offsets-v1"
OFFSET_DTYPE = "<u8"
OFFSET_WRITE_CHUNK = 1_000_000
OFFSET_PROGRESS_INTERVAL = 10_000_000


# =========================
# Utilities
# =========================


def load_config(path="config.json"):
    """Load JSON config file if present."""
    if not os.path.exists(path):
        logger.info("Config file not found, using defaults.")
        return {}
    with open(path, "r") as f:
        return json.load(f)


def set_seed(seed):
    """Ensure deterministic behavior."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


# =========================
# Feature Builder
# =========================


def build_features(fen, perspective):
    """
    Convert FEN string into 768-length NNUE-style binary feature vector.
    Board is flipped for black perspective.
    """

    board_part = fen.split()[0]
    features = np.zeros(INPUT_SIZE, dtype=np.float32)

    rank = 7
    file = 0

    for c in board_part:
        if c == "/":
            rank -= 1
            file = 0
            continue

        if c.isdigit():
            file += int(c)
            continue

        if c not in PIECE_TO_INDEX:
            file += 1
            continue

        sq = rank * 8 + file
        piece_type = PIECE_TO_INDEX[c]
        piece_color = WHITE if c.isupper() else BLACK

        index_color = 1 if piece_color != perspective else 0
        relative_sq = sq if perspective == WHITE else (sq ^ 56)

        idx = 384 * index_color + 64 * piece_type + relative_sq
        if 0 <= idx < INPUT_SIZE:
            features[idx] = 1.0

        file += 1

    return features


# =========================
# Sparse Dataset
# =========================


def offset_index_metadata(path, record_count, complete):
    stat = os.stat(path)
    return {
        "kind": OFFSET_INDEX_KIND,
        "sparse_path": os.path.abspath(path),
        "sparse_bytes": stat.st_size,
        "sparse_mtime_ns": stat.st_mtime_ns,
        "records": record_count,
        "complete": bool(complete),
    }


def write_json_atomic(path, value):
    temporary_path = path + ".part"
    with open(temporary_path, "w", encoding="utf-8", newline="\n") as target:
        json.dump(value, target, indent=2)
        target.write("\n")
        target.flush()
        os.fsync(target.fileno())
    os.replace(temporary_path, path)


def valid_offset_index(
    sparse_path, index_path, metadata_path, required_records=0
):
    if not os.path.isfile(index_path) or not os.path.isfile(metadata_path):
        return None

    try:
        with open(metadata_path, encoding="utf-8") as source:
            metadata = json.load(source)
        stat = os.stat(sparse_path)
        records = int(metadata["records"])
        if (
            metadata.get("kind") != OFFSET_INDEX_KIND
            or int(metadata.get("sparse_bytes", -1)) != stat.st_size
            or int(metadata.get("sparse_mtime_ns", -1)) != stat.st_mtime_ns
            or records <= 0
            or os.path.getsize(index_path) != records * 8
            or (
                int(required_records) > 0
                and records < int(required_records)
                and not bool(metadata.get("complete", False))
            )
            or (
                int(required_records) <= 0
                and not bool(metadata.get("complete", False))
            )
        ):
            return None
        return records
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        return None


def flush_offset_chunk(target, values):
    if not values:
        return
    if sys.byteorder != "little":
        values.byteswap()
    values.tofile(target)


def build_offset_index(
    sparse_path, index_path, metadata_path, record_limit=0
):
    sparse_size = os.path.getsize(sparse_path)
    temporary_index = index_path + ".part"
    os.makedirs(os.path.dirname(os.path.abspath(index_path)), exist_ok=True)

    logger.info("Building compact sparse offset index: %s", index_path)
    logger.info("Sparse dataset bytes: %d", sparse_size)

    started = time.time()
    record_count = 0
    offset = 0
    values = array("Q")

    try:
        with open(
            sparse_path, "rb", buffering=8 * 1024 * 1024
        ) as source, open(
            temporary_index, "wb", buffering=8 * 1024 * 1024
        ) as target:
            while (
                offset < sparse_size
                and (int(record_limit) <= 0 or record_count < int(record_limit))
            ):
                header = source.read(2)
                if len(header) != 2:
                    raise ValueError(
                        f"truncated sparse header at record {record_count + 1:,}"
                    )

                n_stm, n_nstm = header
                if not 2 <= n_stm <= 32 or n_nstm != n_stm:
                    raise ValueError(
                        "invalid sparse counts at record "
                        f"{record_count + 1:,}: {n_stm}, {n_nstm}"
                    )

                record_size = 2 + 2 * n_stm + 2 * n_nstm + 4
                if offset + record_size > sparse_size:
                    raise ValueError(
                        f"truncated sparse payload at record {record_count + 1:,}"
                    )

                values.append(offset)
                record_count += 1
                offset += record_size
                source.seek(record_size - 2, os.SEEK_CUR)

                if len(values) >= OFFSET_WRITE_CHUNK:
                    flush_offset_chunk(target, values)
                    values = array("Q")

                if record_count % OFFSET_PROGRESS_INTERVAL == 0:
                    elapsed = max(time.time() - started, 1e-9)
                    logger.info(
                        "Indexed %d records (%.1f%%, %.0f records/s)",
                        record_count,
                        100.0 * offset / sparse_size,
                        record_count / elapsed,
                    )

            flush_offset_chunk(target, values)
            target.flush()
            os.fsync(target.fileno())

        os.replace(temporary_index, index_path)
        complete = offset == sparse_size
        write_json_atomic(
            metadata_path,
            offset_index_metadata(sparse_path, record_count, complete),
        )
    except Exception:
        logger.exception("Failed while building sparse offset index")
        raise

    logger.info(
        "Sparse offset index ready: %d records in %.1fs (%.1f MiB)",
        record_count,
        time.time() - started,
        os.path.getsize(index_path) / (1024 * 1024),
    )
    return record_count


class SparseDataset(Dataset):
    """Memory-mapped sparse records with a disk-backed uint64 offset index."""

    def __init__(self, path, sample_limit=0, index_path=None):
        self.path = os.path.abspath(path)
        self.index_path = os.path.abspath(index_path or (path + ".offsets.u64"))
        self.metadata_path = self.index_path + ".json"
        self.file = None
        self.mm = None
        self.offsets = None

        record_count = valid_offset_index(
            self.path,
            self.index_path,
            self.metadata_path,
            int(sample_limit),
        )
        if record_count is None:
            record_count = build_offset_index(
                self.path,
                self.index_path,
                self.metadata_path,
                int(sample_limit),
            )
        else:
            logger.info("Using existing sparse offset index: %s", self.index_path)

        self.index_records = record_count
        self.length = (
            min(record_count, int(sample_limit))
            if int(sample_limit) > 0
            else record_count
        )
        self._open_resources()
        logger.info("Dataset size: %d", self.length)

    def _open_resources(self):
        if self.offsets is None:
            self.offsets = np.memmap(
                self.index_path,
                dtype=OFFSET_DTYPE,
                mode="r",
                shape=(self.index_records,),
            )
        if self.mm is None:
            self.file = open(self.path, "rb")
            self.mm = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)

    def __getstate__(self):
        state = self.__dict__.copy()
        state["file"] = None
        state["mm"] = None
        state["offsets"] = None
        return state

    def close(self):
        if self.mm is not None:
            self.mm.close()
            self.mm = None
        if self.file is not None:
            self.file.close()
            self.file = None
        if self.offsets is not None:
            mapped = getattr(self.offsets, "_mmap", None)
            if mapped is not None:
                mapped.close()
            self.offsets = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        self._open_resources()
        offset = int(self.offsets[idx])
        ptr = offset

        n_stm = self.mm[ptr]
        ptr += 1
        n_nstm = self.mm[ptr]
        ptr += 1

        x_stm = np.zeros(INPUT_SIZE, dtype=np.float32)
        x_nstm = np.zeros(INPUT_SIZE, dtype=np.float32)

        stm_indices = np.frombuffer(
            self.mm, dtype="<u2", count=n_stm, offset=ptr
        )
        ptr += 2 * n_stm
        nstm_indices = np.frombuffer(
            self.mm, dtype="<u2", count=n_nstm, offset=ptr
        )
        ptr += 2 * n_nstm

        x_stm[stm_indices] = 1.0
        x_nstm[nstm_indices] = 1.0
        result = struct.unpack_from("<f", self.mm, ptr)[0]

        return (
            torch.from_numpy(x_stm),
            torch.from_numpy(x_nstm),
            torch.tensor(result, dtype=torch.float32),
        )


class DatasetRange(Dataset):
    def __init__(self, dataset, start, length):
        self.dataset = dataset
        self.start = int(start)
        self.length = int(length)

    def __len__(self):
        return self.length

    def __getitem__(self, index):
        return self.start + index


class SparseBatchCollator:
    """Decode one dense batch directly, avoiding per-position tensor churn."""

    def __init__(self, dataset):
        self.dataset = dataset

    def __call__(self, record_indices):
        self.dataset._open_resources()
        batch_size = len(record_indices)
        x_stm = np.zeros((batch_size, INPUT_SIZE), dtype=np.float32)
        x_nstm = np.zeros((batch_size, INPUT_SIZE), dtype=np.float32)
        results = np.empty(batch_size, dtype=np.float32)

        for row, record_index in enumerate(record_indices):
            offset = int(self.dataset.offsets[int(record_index)])
            ptr = offset
            n_stm = self.dataset.mm[ptr]
            ptr += 1
            n_nstm = self.dataset.mm[ptr]
            ptr += 1

            stm_indices = np.frombuffer(
                self.dataset.mm, dtype="<u2", count=n_stm, offset=ptr
            )
            ptr += 2 * n_stm
            nstm_indices = np.frombuffer(
                self.dataset.mm, dtype="<u2", count=n_nstm, offset=ptr
            )
            ptr += 2 * n_nstm

            x_stm[row, stm_indices] = 1.0
            x_nstm[row, nstm_indices] = 1.0
            results[row] = struct.unpack_from("<f", self.dataset.mm, ptr)[0]

        return (
            torch.from_numpy(x_stm),
            torch.from_numpy(x_nstm),
            torch.from_numpy(results),
        )


class BlockShuffleSampler(Sampler):
    """Shuffle large, already-randomized data in blocks using bounded memory."""

    def __init__(self, data_source, block_size=1_000_000, seed=42):
        self.length = len(data_source)
        self.block_size = int(block_size)
        self.seed = int(seed)
        self.epoch = 0
        self.start_position = 0
        if self.block_size <= 0:
            raise ValueError("sampler_block_size must be positive")

    def __len__(self):
        return self.length - self.start_position

    def set_epoch(self, epoch, start_position=0):
        self.epoch = int(epoch)
        self.start_position = int(start_position)
        if not 0 <= self.start_position <= self.length:
            raise ValueError("sampler start position is outside the dataset")

    def __iter__(self):
        block_count = (self.length + self.block_size - 1) // self.block_size
        blocks = list(range(block_count))
        generator = random.Random(self.seed + self.epoch)
        generator.shuffle(blocks)
        skip = self.start_position

        for block in blocks:
            start = block * self.block_size
            stop = min(start + self.block_size, self.length)
            reverse = bool(generator.getrandbits(1))
            block_length = stop - start
            if skip >= block_length:
                skip -= block_length
                continue

            if reverse:
                yield from range(stop - 1 - skip, start - 1, -1)
            else:
                yield from range(start + skip, stop)
            skip = 0


# =========================
# NNUE Model
# =========================


class NNUE(nn.Module):
    """
    Simple NNUE-style architecture:
        shared first layer
        clipped squared activation
        concatenation
        final linear output
    """

    def __init__(self, l1_size):
        super().__init__()
        self.fc1 = nn.Linear(INPUT_SIZE, l1_size)
        self.fc2 = nn.Linear(l1_size * 2, 1)

    def forward(self, x_stm, x_nstm):

        h_stm = torch.clamp(self.fc1(x_stm), 0, 1)
        h_nstm = torch.clamp(self.fc1(x_nstm), 0, 1)

        h_stm = h_stm * h_stm
        h_nstm = h_nstm * h_nstm

        h = torch.cat([h_stm, h_nstm], dim=1)
        out = self.fc2(h)

        return out.squeeze(1)


# =========================
# Export Quantized Model
# =========================


def export_model(model, path, scale):

    fc1_w = model.fc1.weight.detach().cpu().numpy()
    fc1_b = model.fc1.bias.detach().cpu().numpy()
    fc2_w = model.fc2.weight.detach().cpu().numpy()
    fc2_b = model.fc2.bias.detach().cpu().numpy()

    l1_size = fc1_w.shape[0]

    tmp_path = path + ".tmp"
    with open(tmp_path, "wb") as f:

        # fc1 weights
        for i in range(INPUT_SIZE):
            for j in range(l1_size):
                val = int(round(fc1_w[j][i] * scale))
                val = max(-32768, min(32767, val))
                f.write(struct.pack("<h", val))

        # fc1 bias (none in model → write zeros)
        for j in range(l1_size):
            val = int(round(fc1_b[j] * scale))
            val = max(-32768, min(32767, val))
            f.write(struct.pack("<h", val))

        # fc2 weights
        for j in range(l1_size * 2):
            val = int(round(fc2_w[0][j] * scale))
            val = max(-32768, min(32767, val))
            f.write(struct.pack("<h", val))

        # fc2 bias
        val = int(round(fc2_b[0] * scale))
        val = max(-32768, min(32767, val))
        f.write(struct.pack("<h", val))

    os.replace(tmp_path, path)


# =========================
# Training
# =========================


def main():

    config_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.environ.get("NULLSTAR_TRAINING_CONFIG", "config.json")
    )
    config = load_config(config_path)
    configure_logging(config.get("log_path", "training.log"))

    set_seed(config.get("seed", 42))

    # Device selection from config
    device_cfg = config.get("device", "auto")
    if device_cfg == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(device_cfg)

    logger.info("Using device: %s", device)

    use_gpu = device.type == "cuda"

    # Only enable AMP if CUDA is available
    use_amp = config.get("use_amp", True) and device.type == "cuda"

    dataset = SparseDataset(
        config.get("training_file", "training_sparse.bin"),
        config.get("dataset_sample_limit", 0),
        config.get("offset_index_path"),
    )

    val_split = config.get("validation_split", 0.05)
    val_size = int(len(dataset) * val_split)
    train_size = len(dataset) - val_size
    if train_size <= 0 or val_size <= 0:
        raise ValueError(
            f"invalid training/validation split: {train_size}, {val_size}"
        )

    # The sparse corpus is already shuffled. Contiguous views avoid creating
    # hundreds of millions of Python integer indices for random_split().
    train_set = DatasetRange(dataset, 0, train_size)
    val_set = DatasetRange(dataset, train_size, val_size)
    train_sampler = BlockShuffleSampler(
        train_set,
        config.get("sampler_block_size", 1_000_000),
        config.get("seed", 42),
    )
    logger.info("Training positions: %d", train_size)
    logger.info("Validation positions: %d", val_size)
    batch_size = int(config.get("batch_size", 256))
    collator = SparseBatchCollator(dataset)

    train_loader = DataLoader(
        train_set,
        batch_size=batch_size,
        sampler=train_sampler,
        num_workers=config.get("num_workers", 0),
        pin_memory=use_gpu,
        collate_fn=collator,
    )

    val_loader = DataLoader(
        val_set,
        batch_size=batch_size,
        shuffle=False,
        num_workers=config.get("num_workers", 0),
        pin_memory=use_gpu,
        collate_fn=collator,
    )

    model = NNUE(config.get("l1_size", 128)).to(device)

    optimizer = optim.Adam(model.parameters(), lr=config.get("learning_rate", 1e-3))

    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        factor=config.get("lr_decay_factor", 0.5),
        patience=config.get("lr_patience", 3)
    )

    criterion = nn.BCEWithLogitsLoss()

    # NEW AMP API (future-proof)
    if hasattr(torch, "amp"):
        scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    else:
        scaler = torch.cuda.amp.GradScaler(enabled=use_amp)

    start_epoch = 0
    resume_batch = 0
    best_val_loss = float("inf")

    # Resume
    checkpoint_path = config.get("checkpoint_path", "checkpoint.pt")
    mid_checkpoint_path = config.get(
        "mid_checkpoint_path", "checkpoint_mid_epoch.pt"
    )
    export_path = config.get("export_path", "network.bin")

    resume_candidates = []
    for candidate_path, is_mid_epoch in (
        (checkpoint_path, False),
        (mid_checkpoint_path, True),
    ):
        if not os.path.exists(candidate_path):
            continue

        candidate = torch.load(candidate_path, map_location=device)
        candidate_epoch = int(candidate["epoch"])
        candidate_batch = (
            int(candidate.get("batches_completed", 0))
            if is_mid_epoch
            else 0
        )
        resume_candidates.append((
            candidate_epoch,
            candidate_batch,
            os.path.getmtime(candidate_path),
            candidate_path,
            is_mid_epoch,
            candidate,
        ))

    if resume_candidates:
        (
            _,
            _,
            _,
            resume_path,
            resume_is_mid_epoch,
            checkpoint,
        ) = max(resume_candidates, key=lambda item: item[:3])
        logger.info("Resuming from checkpoint: %s", resume_path)
        model.load_state_dict(checkpoint["model"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        if "scheduler" in checkpoint:
            scheduler.load_state_dict(checkpoint["scheduler"])
        start_epoch = int(checkpoint["epoch"])
        best_val_loss = float(checkpoint["best_val_loss"])
        if resume_is_mid_epoch:
            resume_batch = int(checkpoint.get(
                "batches_completed",
                config.get("resume_mid_epoch_batch", 0),
            ))
            logger.info(
                "Resuming epoch %d at batch %d",
                start_epoch + 1,
                resume_batch,
            )

    epochs = config.get("epochs", 10)
    log_every = config.get("log_every", 5000)
    mid_checkpoint_every = config.get("mid_checkpoint_every", 10000)

    label_smoothing = config.get("label_smoothing", 0.0)
    grad_clip = config.get("grad_clip", 0.0)

    for epoch in range(start_epoch, epochs):

        logger.info("\nEpoch %d/%d", epoch + 1, epochs)
        epoch_resume_batch = resume_batch if epoch == start_epoch else 0
        resume_position = min(epoch_resume_batch * batch_size, train_size)
        train_sampler.set_epoch(epoch, resume_position)
        model.train()

        train_loss = 0.0
        processed_batches = 0
        start_time = time.time()
        full_epoch_batches = (train_size + batch_size - 1) // batch_size

        for local_batch_idx, (xb_stm, xb_nstm, yb) in enumerate(train_loader):

            batch_idx = epoch_resume_batch + local_batch_idx

            xb_stm = xb_stm.to(device)
            xb_nstm = xb_nstm.to(device)
            yb = yb.to(device)

            # Optional label smoothing
            if label_smoothing > 0:
                yb = yb * (1 - label_smoothing) + label_smoothing * 0.5

            optimizer.zero_grad()

            if use_amp:

                with torch.cuda.amp.autocast(enabled=True):
                    pred = model(xb_stm, xb_nstm)
                    loss = criterion(pred, yb)

                scaler.scale(loss).backward()

                if grad_clip > 0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)

                scaler.step(optimizer)
                scaler.update()

            else:

                pred = model(xb_stm, xb_nstm)
                loss = criterion(pred, yb)

                loss.backward()

                if grad_clip > 0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)

                optimizer.step()

            train_loss += loss.item()
            processed_batches += 1

            # progress logging
            # Determine triggers
            log_trigger = log_every > 0 and batch_idx % log_every == 0 and batch_idx > 0

            checkpoint_trigger = (
                mid_checkpoint_every > 0
                and batch_idx % mid_checkpoint_every == 0
                and batch_idx > 0
            )

            # Only proceed if either event happens
            if log_trigger or checkpoint_trigger:

                message = ""

                # Build full progress line only if it's a log interval
                if log_trigger:

                    elapsed = time.time() - start_time
                    rate = processed_batches / elapsed
                    remaining = (full_epoch_batches - batch_idx) / rate

                    elapsed_h = int(elapsed // 3600)
                    elapsed_m = int((elapsed % 3600) // 60)
                    elapsed_s = int(elapsed % 60)

                    message = (
                        f"Epoch {epoch+1} | "
                        f"{batch_idx}/{full_epoch_batches} "
                        f"({100*batch_idx/full_epoch_batches:.1f}%) | "
                        f"{rate:.1f} it/s | "
                        f"Elapsed {elapsed_h:02d}:{elapsed_m:02d}:{elapsed_s:02d} | "
                        f"ETA {remaining/60:.1f} min"
                    )

                # Run checkpoint independently
                if checkpoint_trigger:

                    state = {
                        "epoch": epoch,
                        "batches_completed": batch_idx + 1,
                        "model": model.state_dict(),
                        "optimizer": optimizer.state_dict(),
                        "scheduler": scheduler.state_dict(),
                        "best_val_loss": best_val_loss,
                    }

                    tmp_path = mid_checkpoint_path + ".tmp"
                    torch.save(state, tmp_path)
                    os.replace(tmp_path, mid_checkpoint_path)

                    if not message:
                        # If checkpoint fires without log firing,
                        # build minimal message so formatting stays clean
                        message = (
                            f"Epoch {epoch+1} | "
                            f"{batch_idx}/{full_epoch_batches}"
                        )

                    message += " | checkpoint saved"

                logger.info(message)
        # ---- end batch loop ----

        if processed_batches == 0:
            raise RuntimeError("no training batches were processed")
        train_loss /= processed_batches
        resume_batch = 0

        # Validation
        model.eval()
        val_loss = 0.0

        with torch.no_grad():
            for xb_stm, xb_nstm, yb in val_loader:

                xb_stm = xb_stm.to(device)
                xb_nstm = xb_nstm.to(device)
                yb = yb.to(device)

                pred = model(xb_stm, xb_nstm)
                loss = criterion(pred, yb)

                val_loss += loss.item()

        val_loss /= len(val_loader)

        scheduler.step(val_loss)

        logger.info("Current LR: %s", optimizer.param_groups[0]["lr"])
        logger.info("Train Loss: %.6f", train_loss)
        logger.info("Val Loss:   %.6f", val_loss)

        # Save best model
        if val_loss < best_val_loss:

            best_val_loss = val_loss

            best_path = config.get("best_model_path", "best_model.pt")

            tmp_path = best_path + ".tmp"

            torch.save(model.state_dict(), tmp_path)

            os.replace(tmp_path, best_path)

            export_model(model, export_path, config.get("scale", 128))

            logger.info(f"Saved best model and exported {export_path}")

            print("Network size:", os.path.getsize(export_path))

        state = {
            "epoch": epoch + 1,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "scheduler": scheduler.state_dict(),
            "best_val_loss": best_val_loss,
        }

        tmp_path = checkpoint_path + ".tmp"
        torch.save(state, tmp_path)
        os.replace(tmp_path, checkpoint_path)

        if config.get("save_epoch_networks", True):
            export_root, export_extension = os.path.splitext(export_path)
            export_model(
                model,
                f"{export_root}_epoch_{epoch+1}{export_extension}",
                config.get("scale", 128),
            )

if __name__ == "__main__":
    main()
