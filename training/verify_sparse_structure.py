# verify_sparse_structure.py
# jasper sinclair
#
# Simple integrity check for the sparse NNUE training dataset.
#
# This script scans the binary file produced by convert_to_sparse.py
# and verifies that all stored feature indices are valid.
#
# Dataset record layout:
#
#   uint8   n_stm             number of side-to-move features
#   uint8   n_nstm            number of opponent features
#   uint16  stm_indices[]     sparse feature indices
#   uint16  nstm_indices[]    sparse feature indices
#   float32 result            training target
#
# Each index must be within the valid NNUE feature range:
#
#   0 <= index < 768
#
# If any index is outside this range, the dataset is corrupted.

import json
import math
import os
import struct

INPUT_SIZE = 768


# =========================
# Config loader
# =========================

def load_config(path=None):
    path = path or os.environ.get("NULLSTAR_TRAINING_CONFIG", "config.json")
    """Load configuration file if present."""
    if not os.path.exists(path):
        return {}

    with open(path, "r") as f:
        return json.load(f)


# =========================
# Main verification
# =========================

def main():

    config = load_config()

    # Dataset path from config
    sparse_path = config.get("training_file", "training_sparse.bin")

    # Optional limit (useful for quickly checking large datasets)
    sample_limit = config.get("structure_verify_limit", 1_000_000)

    # Progress interval (how often to print progress)
    progress_interval = config.get("verify_progress_interval", 1_000_000)

    print("Verifying dataset:", sparse_path)

    checked = 0

    # Open sparse training dataset
    with open(sparse_path, "rb") as f:

        while True:

            # Optional limit for quick verification
            if sample_limit and checked >= sample_limit:
                break

            # Read record header (2 bytes)
            header = f.read(2)

            # End of file
            if not header:
                break

            # Safety check for truncated file
            if len(header) < 2:
                print("ERROR: truncated record header")
                return 1

            # Number of sparse features for each perspective
            n_stm, n_nstm = header
            if not 2 <= n_stm <= 32 or n_nstm != n_stm:
                print(
                    "ERROR: invalid feature counts at record",
                    f"{checked + 1:,}",
                    n_stm,
                    n_nstm,
                )
                return 1

            # -------------------------
            # Verify side-to-move feature indices
            # -------------------------
            for _ in range(n_stm):

                # Each index is stored as uint16
                data = f.read(2)

                if len(data) < 2:
                    print("ERROR: truncated side-to-move index")
                    return 1

                idx = struct.unpack("<H", data)[0]

                # Feature index must be within NNUE input range
                if idx >= INPUT_SIZE:
                    print("ERROR: bad side-to-move index", idx)
                    return 1

            # -------------------------
            # Verify opponent feature indices
            # -------------------------
            for _ in range(n_nstm):

                data = f.read(2)

                if len(data) < 2:
                    print("ERROR: truncated opponent index")
                    return 1

                idx = struct.unpack("<H", data)[0]

                if idx >= INPUT_SIZE:
                    print("ERROR: bad opponent index", idx)
                    return 1

            # Skip result value (float32)
            result_bytes = f.read(4)

            if len(result_bytes) < 4:
                print("ERROR: truncated result value")
                return 1

            result = struct.unpack("<f", result_bytes)[0]
            if not math.isfinite(result) or not 0.0 <= result <= 1.0:
                print("ERROR: invalid result at record", f"{checked + 1:,}")
                return 1

            checked += 1

            # Progress indicator
            if progress_interval and checked % progress_interval == 0:
                print(f"checked {checked:,} records")

    print("Verified sparse structure OK")
    print("Records checked:", checked)
    if sample_limit:
        print("Verification limit:", sample_limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
