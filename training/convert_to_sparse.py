# convert_to_sparse.py
# jasper sinclair
#
# Converts dense FEN-based training data into a compact sparse binary format
# suitable for fast memory-mapped loading during NNUE training.
#
# Input format (training.txt):
#     <FEN>|<result>
#
# Output format (training_sparse.bin), per position:
#     uint8  n_stm
#     uint8  n_nstm
#     uint16 stm_indices[n_stm]
#     uint16 nstm_indices[n_nstm]
#     float32 result
#
# Each record stores active feature indices instead of full 768-length vectors,
# reducing disk usage and improving loading speed.

import struct
import json
import math
import os
import random
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **_):
        return iterable

# =========================
# Constants
# =========================

# 6 piece types × 64 squares × 2 (us / them)
INPUT_SIZE = 768
WHITE = 0
BLACK = 1

# Piece type mapping.
# Color is handled separately via perspective logic.
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


def load_config(path=None):
    path = path or os.environ.get("NULLSTAR_TRAINING_CONFIG", "config.json")
    if not os.path.exists(path):
        return {}

    with open(path, "r") as f:
        return json.load(f)


# =========================
# Parsing
# =========================


def parse_epd_line(line):

    line = line.strip()

    if not line:
        return None, None

    # -----------------------------------------
    # Format: FEN | result   (selfplay)
    # -----------------------------------------
    if "|" in line:
        try:
            fen_part, score_part = line.split("|", 1)
            fen = " ".join(fen_part.strip().split()[:4])
            result = float(score_part.strip())
            if not math.isfinite(result) or not 0.0 <= result <= 1.0:
                return None, None
            return fen, result
        except:
            pass


    # -----------------------------------------
    # Format: EPD  c9 "1-0"
    # -----------------------------------------
    if '"' in line:
        try:
            result_str = line.split('"')[1]

            if result_str == "1-0":
                result = 1.0
            elif result_str == "0-1":
                result = 0.0
            elif result_str == "1/2-1/2":
                result = 0.5
            else:
                return None, None

            tokens = line.split()
            fen = " ".join(tokens[:4])
            return fen, result
        except:
            pass


    # -----------------------------------------
    # Format: bracket result   [0.5]
    # -----------------------------------------
    if "[" in line and "]" in line:
        try:
            result = float(line.split("[")[1].split("]")[0])
            tokens = line.split()
            fen = " ".join(tokens[:4])
            return fen, result
        except:
            pass


    # -----------------------------------------
    # Format: numeric eval at end
    # convert eval -> probability
    # -----------------------------------------
    tokens = line.split()

    if len(tokens) >= 5:
        try:
            val = float(tokens[-1])

            # If already probability
            if 0.0 <= val <= 1.0:
                result = val
            else:
                # Convert centipawn to probability
                import math
                result = 1.0 / (1.0 + math.exp(-val / 400.0))

            fen = " ".join(tokens[:4])
            return fen, result
        except:
            pass


    return None, None


# =========================
# Feature extraction
# =========================


def extract_indices(fen, perspective):
    """
    Extract active NNUE feature indices from a FEN string.

    Features are encoded relative to a given perspective:
        - Own pieces occupy first 384 indices
        - Opponent pieces occupy second 384 indices
        - Board is vertically flipped for black perspective

    Returns:
        List of active feature indices (sparse representation).
    """

    board_part = fen.split()[0]
    indices = []

    rank = 7
    file = 0

    for c in board_part:
        # Move to next rank
        if c == "/":
            rank -= 1
            file = 0
            continue

        # Skip empty squares
        if c.isdigit():
            file += int(c)
            continue

        # Skip unsupported symbols
        if c not in PIECE_TO_INDEX:
            file += 1
            continue

        # Convert (rank, file) into square index 0–63
        sq = rank * 8 + file

        piece_type = PIECE_TO_INDEX[c]
        piece_color = WHITE if c.isupper() else BLACK

        # Determine whether piece belongs to perspective side
        index_color = 1 if piece_color != perspective else 0

        # Flip board vertically for black perspective
        relative_sq = sq if perspective == WHITE else (sq ^ 56)

        # Compute final 0–767 feature index
        idx = 384 * index_color + 64 * piece_type + relative_sq
        indices.append(idx)

        file += 1

    return indices


def orient_position(fen, result, label_perspective):
    """Return features and target in the engine's STM/NSTM order."""

    white_indices = extract_indices(fen, WHITE)
    black_indices = extract_indices(fen, BLACK)
    side_to_move = fen.split()[1]

    if side_to_move == "w":
        return white_indices, black_indices, result

    if side_to_move == "b":
        if label_perspective == "white":
            result = 1.0 - result
        return black_indices, white_indices, result

    raise ValueError(f"invalid side-to-move field: {side_to_move!r}")


# =========================
# Conversion Pipeline
# =========================


def convert(
    input_path,
    output_path,
    skip_invalid=True,
    sample_limit=0,
    label_perspective="side_to_move",
):

    if label_perspective not in {"side_to_move", "white"}:
        raise ValueError(
            "label_perspective must be 'side_to_move' or 'white'"
        )

    valid = 0
    invalid = 0

    total_lines = (
        sample_limit
        if sample_limit > 0
        else sum(1 for _ in open(input_path, "r"))
    )

    with open(input_path, "r") as fin, open(output_path, "wb") as fout:

        for i, line in enumerate(tqdm(fin, total=total_lines)):

            # Optional dataset size limit
            if sample_limit > 0 and i >= sample_limit:
                break

            fen, result = parse_epd_line(line)

            if fen is None:
                invalid += 1
                if not skip_invalid:
                    raise ValueError(f"invalid training record at line {i + 1:,}")
                continue

            try:
                stm_indices, nstm_indices, result = orient_position(
                    fen, result, label_perspective
                )
            except ValueError as error:
                invalid += 1
                if not skip_invalid:
                    raise ValueError(
                        f"invalid training record at line {i + 1:,}"
                    ) from error
                continue

            # ---------------------------------
            # Write binary record
            # ---------------------------------

            record = bytearray()

            # Write feature counts
            record += struct.pack("B", len(stm_indices))
            record += struct.pack("B", len(nstm_indices))

            # Write side-to-move feature indices (uint16) - batch packed
            if stm_indices:
                record += struct.pack(f"<{len(stm_indices)}H", *stm_indices)

            # Write opponent feature indices (uint16) - batch packed
            if nstm_indices:
                record += struct.pack(f"<{len(nstm_indices)}H", *nstm_indices)

            # Write training target (float32)
            record += struct.pack("<f", result)

            fout.write(record)

            valid += 1

    return valid, invalid


# =========================
# Entry Point
# =========================

if __name__ == "__main__":

    config = load_config()

    input_path = config.get("training_txt", "training.txt")
    output_path = config.get("training_file", "training_sparse.bin")
    skip_invalid = config.get("skip_invalid", True)
    label_perspective = config.get("label_perspective", "side_to_move")

    dataset_sample_limit = config.get("dataset_sample_limit", 0)

    print("Input:", input_path)
    print("Output:", output_path)
    print("Label perspective:", label_perspective)

    valid, invalid = convert(
        input_path,
        output_path,
        skip_invalid,
        dataset_sample_limit,
        label_perspective
    )

    print(f"\nValid positions:   {valid}")
    print(f"Skipped positions: {invalid}")
