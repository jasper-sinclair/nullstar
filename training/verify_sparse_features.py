# verify_sparse_features.py
# jasper sinclair
#
# Verifies correctness of training_sparse.bin by comparing it against
# the original training dataset used for conversion.
#
# This script:
#   1. Rebuilds dense features from FEN (text version)
#   2. Reconstructs dense features from sparse binary
#   3. Compares both representations
#   4. Verifies result value matches

import struct
import random
import numpy as np
import json
import os

# =========================
# Constants
# =========================

INPUT_SIZE = 768

WHITE = 0
BLACK = 1

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


# =========================
# Config loader
# =========================


def load_config(path="config.json"):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


# =========================
# Parsing
# =========================


def parse_epd_line(line):

    line = line.strip()

    if "|" not in line:
        return None, None

    try:
        fen_part, score_part = line.split("|", 1)
        fen = " ".join(fen_part.strip().split()[:4])
        result = float(score_part.strip())
        return fen, result
    except:
        return None, None


# =========================
# Feature Builder
# =========================


def build_features(fen, perspective):

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
        features[idx] = 1.0

        file += 1

    return features


# =========================
# Build filtered dataset
# =========================


def build_filtered_dataset(epd_path, sample_limit=0):

    dataset = []

    # Match convert_to_sparse.py behavior:
    # load all lines first
    with open(epd_path, "r") as f:
        for line in f:

            fen, result = parse_epd_line(line)

            if fen is None:
                continue

            dataset.append((fen, result))

            # Optional dataset limit
            if sample_limit and len(dataset) >= sample_limit:
                break

    return dataset


# =========================
# Compute binary offsets
# =========================


def compute_offsets(sparse_path):

    offsets = []

    with open(sparse_path, "rb") as f:

        pos = 0

        while True:

            header = f.read(2)
            if not header:
                break

            n_stm = header[0]
            n_nstm = header[1]

            record_size = 2 + 2 * n_stm + 2 * n_nstm + 4

            offsets.append(pos)

            f.seek(record_size - 2, 1)

            pos += record_size

    return offsets


# =========================
# Main verification
# =========================


def main():

    config = load_config()

    sparse_path = config.get("training_file", "training_sparse.bin")
    epd_path = config.get("verification_epd", "quiet.epd")

    dataset_sample_limit = config.get("dataset_sample_limit", 0)
    verification_samples = config.get("verification_samples", 10)
    label_perspective = config.get("label_perspective", "side_to_move")
    random.seed(config.get("seed", 42))

    print("Sparse dataset:", sparse_path)
    print("EPD reference:", epd_path)

    offsets = compute_offsets(sparse_path)

    print("Binary dataset size:", len(offsets))

    dataset = build_filtered_dataset(
        epd_path,
        dataset_sample_limit
    )

    print("Filtered dataset size:", len(dataset))

    if len(dataset) != len(offsets):
        print("WARNING: dataset sizes differ")

    # =========================
    # Random verification
    # =========================

    for _ in range(verification_samples):

        idx = random.randint(0, min(len(dataset), len(offsets)) - 1)

        fen, result = dataset[idx]

        x_white = build_features(fen, WHITE)
        x_black = build_features(fen, BLACK)

        if fen.split()[1] == "w":
            x_stm_txt, x_nstm_txt = x_white, x_black
            expected_result = result
        else:
            x_stm_txt, x_nstm_txt = x_black, x_white
            expected_result = (
                1.0 - result if label_perspective == "white" else result
            )

        with open(sparse_path, "rb") as f:

            f.seek(offsets[idx])

            header = f.read(2)
            n_stm = header[0]
            n_nstm = header[1]

            record_size = 2 + 2 * n_stm + 2 * n_nstm + 4

            data = header + f.read(record_size - 2)

        offset = 2

        stm_indices = struct.unpack_from(f"<{n_stm}H", data, offset)
        offset += 2 * n_stm

        nstm_indices = struct.unpack_from(f"<{n_nstm}H", data, offset)
        offset += 2 * n_nstm

        result_bin = struct.unpack_from("<f", data, offset)[0]

        x_stm_bin = np.zeros(INPUT_SIZE, dtype=np.float32)
        x_nstm_bin = np.zeros(INPUT_SIZE, dtype=np.float32)

        x_stm_bin[list(stm_indices)] = 1.0
        x_nstm_bin[list(nstm_indices)] = 1.0

        if not np.allclose(x_stm_txt, x_stm_bin):
            print("Mismatch at index", idx)
            print("TXT active:", np.nonzero(x_stm_txt)[0][:10])
            print("BIN active:", np.nonzero(x_stm_bin)[0][:10])
            break

        assert np.allclose(x_stm_txt, x_stm_bin)
        assert np.allclose(x_nstm_txt, x_nstm_bin)
        assert abs(expected_result - result_bin) < 1e-6

    print("✅ Verification passed.")


if __name__ == "__main__":
    main()
