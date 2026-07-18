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

import struct
import json
import os
import random

INPUT_SIZE = 768


# =========================
# Config loader
# =========================

def load_config(path="config.json"):
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
    sample_limit = config.get("dataset_sample_limit", 0)

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
                print("WARNING: truncated record header")
                break

            # Number of sparse features for each perspective
            n_stm, n_nstm = header

            # -------------------------
            # Verify side-to-move feature indices
            # -------------------------
            for _ in range(n_stm):

                # Each index is stored as uint16
                data = f.read(2)

                if len(data) < 2:
                    print("WARNING: truncated side-to-move index")
                    return

                idx = struct.unpack("<H", data)[0]

                # Feature index must be within NNUE input range
                if idx >= INPUT_SIZE:
                    print("BAD INDEX", idx)
                    return

            # -------------------------
            # Verify opponent feature indices
            # -------------------------
            for _ in range(n_nstm):

                data = f.read(2)

                if len(data) < 2:
                    print("WARNING: truncated opponent index")
                    return

                idx = struct.unpack("<H", data)[0]

                if idx >= INPUT_SIZE:
                    print("BAD INDEX", idx)
                    return

            # Skip result value (float32)
            result_bytes = f.read(4)

            if len(result_bytes) < 4:
                print("WARNING: truncated result value")
                return

            checked += 1

            # Progress indicator
            if progress_interval and checked % progress_interval == 0:
                print(f"checked {checked:,} records")

    print("Dataset OK")
    print("Records checked:", checked)


if __name__ == "__main__":
    main()
