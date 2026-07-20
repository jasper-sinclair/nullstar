# shuffle_training_txt.py
# jasper sinclair

import json
import os
import random
import shutil
import tempfile
import time


def load_config(path=None):
    path = path or os.environ.get("NULLSTAR_TRAINING_CONFIG", "config.json")
    if not os.path.exists(path):
        print("Config not found, using defaults.")
        return {}
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def write_chunk(lines, directory, chunk_id):
    random.shuffle(lines)
    path = os.path.join(directory, f"chunk_{chunk_id:06d}.bin")
    with open(path, "wb", buffering=8 * 1024 * 1024) as target:
        target.writelines(lines)
    print(f"chunk {chunk_id}", flush=True)
    return path


def main():
    config = load_config()

    seed = config.get("seed")
    if seed is not None:
        random.seed(seed)

    input_file = config.get("shuffle_input", "training.txt")
    output_file = os.path.abspath(
        config.get("shuffle_output", "training_shuffled.txt")
    )
    chunk_size = int(config.get("shuffle_chunk_size", 1_000_000))
    if chunk_size <= 0:
        raise ValueError("shuffle_chunk_size must be positive")

    output_parent = os.path.dirname(output_file)
    os.makedirs(output_parent, exist_ok=True)
    temporary_output = output_file + ".part"

    print("Input :", input_file)
    print("Output:", output_file)
    print("Temporary output:", temporary_output)
    print("Chunk size:", f"{chunk_size:,}")
    print("\nSplitting dataset into shuffled chunks...")

    started = time.time()
    input_records = 0
    expected_bytes = 0

    try:
        with tempfile.TemporaryDirectory(
            prefix=".nullstar_shuffle_", dir=output_parent
        ) as temporary_directory:
            chunk_paths = []
            chunk = []
            chunk_id = 0

            with open(input_file, "rb", buffering=8 * 1024 * 1024) as source:
                for line in source:
                    if not line.endswith((b"\n", b"\r")):
                        line += b"\n"
                    chunk.append(line)
                    input_records += 1
                    expected_bytes += len(line)

                    if len(chunk) >= chunk_size:
                        chunk_id += 1
                        chunk_paths.append(write_chunk(
                            chunk, temporary_directory, chunk_id
                        ))
                        chunk = []

                if chunk:
                    chunk_id += 1
                    chunk_paths.append(write_chunk(
                        chunk, temporary_directory, chunk_id
                    ))

            if not chunk_paths:
                raise ValueError("training input is empty")

            print("\nMerging chunks...")
            random.shuffle(chunk_paths)
            with open(
                temporary_output, "wb", buffering=8 * 1024 * 1024
            ) as destination:
                for path in chunk_paths:
                    with open(path, "rb", buffering=8 * 1024 * 1024) as source:
                        shutil.copyfileobj(source, destination, 8 * 1024 * 1024)
                destination.flush()
                os.fsync(destination.fileno())

            actual_bytes = os.path.getsize(temporary_output)
            if actual_bytes != expected_bytes:
                raise OSError(
                    "shuffled byte-count mismatch: "
                    f"expected {expected_bytes:,}, wrote {actual_bytes:,}"
                )

            os.replace(temporary_output, output_file)
    except Exception:
        print(f"Incomplete shuffled output retained as: {temporary_output}")
        raise

    elapsed = time.time() - started
    print(f"\nRecords: {input_records:,}")
    print(f"Bytes:   {expected_bytes:,}")
    print(f"Shuffle complete in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
