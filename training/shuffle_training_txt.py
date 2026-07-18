# shuffle_training_txt.py
# jasper sinclair

import json
import random
import os
import tempfile
import time


# =========================
# Config
# =========================

def load_config(path="config.json"):
    if not os.path.exists(path):
        print("Config not found, using defaults.")
        return {}
    with open(path) as f:
        return json.load(f)


# =========================
# Main
# =========================

def main():

    config = load_config()

    seed = config.get("seed", None)
    if seed is not None:
        random.seed(seed)

    input_file = config.get("shuffle_input", "training.txt")
    output_file = config.get("shuffle_output", "training_shuffled.txt")

    chunk_size = config.get("shuffle_chunk_size", 1_000_000)

    print("Input :", input_file)
    print("Output:", output_file)
    print("Chunk size:", f"{chunk_size:,}")

    tmp_files = []

    print("\nSplitting dataset into shuffled chunks...")

    start = time.time()

# ---- load file ----
    with open(input_file) as f:

        chunk = []
        chunk_id = 0

        for line in f:

            chunk.append(line)

            if len(chunk) >= chunk_size:

                random.shuffle(chunk)

                tmp = tempfile.NamedTemporaryFile(delete=False, mode="w")

                tmp.writelines(chunk)
                tmp.close()

                tmp_files.append(tmp.name)

                chunk = []
                chunk_id += 1

                print(f"chunk {chunk_id}")

        if chunk:
            random.shuffle(chunk)

            tmp = tempfile.NamedTemporaryFile(delete=False, mode="w")
            tmp.writelines(chunk)
            tmp.close()

            tmp_files.append(tmp.name)

    print("\nMerging chunks...")

    with open(output_file, "w") as out:

        while tmp_files:

            file = random.choice(tmp_files)

            with open(file) as f:
                for line in f:
                    out.write(line)

            os.remove(file)
            tmp_files.remove(file)

    elapsed = time.time() - start

    print(f"\nShuffle complete in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
