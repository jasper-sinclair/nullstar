# verify_training_txt.py
# jasper sinclair

import json
import math
import os
import sys
import time
from collections import Counter


PIECES = frozenset("PNBRQKpnbrqk")


def load_config(path=None):
    path = path or os.environ.get("NULLSTAR_TRAINING_CONFIG", "config.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def valid_placement(placement):
    ranks = placement.split("/")
    if len(ranks) != 8:
        return False

    for rank in ranks:
        width = 0
        for char in rank:
            if char in PIECES:
                width += 1
            elif char in "12345678":
                width += int(char)
            else:
                return False
        if width != 8:
            return False

    return True


def piece_count(placement):
    return sum(char in PIECES for char in placement)


def split_record(line):
    if "|" in line:
        fen, label = line.rsplit("|", 1)
        return fen.strip(), label.strip()

    if "[" in line and "]" in line:
        fen = " ".join(line.split()[:4])
        return fen, line.split("[", 1)[1].split("]", 1)[0]

    if '"' in line:
        fen = " ".join(line.split()[:4])
        result = line.split('"', 2)[1]
        labels = {"1-0": "1.0", "0-1": "0.0", "1/2-1/2": "0.5"}
        return fen, labels.get(result)

    return None, None


def main():
    config = load_config()
    dataset_path = config.get("raw_training_txt", "training.txt")
    max_sample = int(config.get("verify_sample_limit", 500000))
    show_exact = bool(config.get("verify_exact_label_distribution", True))
    max_hash = int(config.get("verify_max_hash", 2_000_000))

    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]

    if not os.path.isfile(dataset_path):
        print(f"Dataset not found: {dataset_path}", file=sys.stderr)
        return 2

    file_size = os.path.getsize(dataset_path)
    if file_size == 0:
        print(f"Dataset is empty: {dataset_path}", file=sys.stderr)
        return 2

    print("Checking dataset:", dataset_path)
    print("Sample limit:", max_sample)

    total = 0
    valid = 0
    bad_fen = 0
    bad_label = 0
    decode_errors = 0
    ctrlz = 0
    duplicates = 0

    label_counts = Counter()
    bucket_counts = Counter()
    piece_count_total = 0
    boards_seen = set()
    first_errors = []
    error_limit = int(config.get("verification_error_examples", 5))

    def remember(kind, line_number, value):
        if len(first_errors) >= error_limit:
            return
        if isinstance(value, bytes):
            preview = value[:240].decode("utf-8", errors="backslashreplace")
        else:
            preview = str(value)[:240]
        first_errors.append((kind, line_number, preview.rstrip()))

    start = time.time()
    last_print = start

    with open(dataset_path, "rb") as source:
        for raw_line in source:
            total += 1

            if b"\x1a" in raw_line:
                ctrlz += 1
                remember("Ctrl-Z marker", total, raw_line)

            try:
                line = raw_line.decode("utf-8").strip()
            except UnicodeDecodeError:
                decode_errors += 1
                remember("UTF-8 decode error", total, raw_line)
                continue

            fen, label_text = split_record(line)
            if label_text is None:
                bad_label += 1
                remember("bad label", total, line)
                continue

            try:
                label = float(label_text)
            except (TypeError, ValueError):
                bad_label += 1
                remember("bad label", total, line)
                continue

            if not math.isfinite(label) or not 0.0 <= label <= 1.0:
                bad_label += 1
                remember("out-of-range label", total, line)
                continue

            tokens = fen.split()
            if (len(tokens) < 2 or tokens[1] not in {"w", "b"}
                    or not valid_placement(tokens[0])):
                bad_fen += 1
                remember("broken FEN", total, line)
                continue

            placement, side = tokens[0], tokens[1]
            valid += 1

            if show_exact:
                label_counts[label] += 1
            bucket_counts[int(label * 100) / 100.0] += 1
            piece_count_total += piece_count(placement)

            key = f"{placement} {side}"
            if key in boards_seen:
                duplicates += 1
            elif len(boards_seen) < max_hash:
                boards_seen.add(key)

            now = time.time()
            if now - last_print > 1:
                percent = source.tell() / file_size * 100
                elapsed = now - start
                speed = total / elapsed if elapsed else 0
                print(
                    f"\rProcessed {total:,} ({percent:.2f}%) "
                    f"{speed:,.0f} positions/s",
                    end="",
                )
                last_print = now

            if max_sample and total >= max_sample:
                break

    print("\n\nLines sampled:", total)
    print("Valid positions:", valid)

    if show_exact and valid:
        print("\nExact label distribution:")
        for label in sorted(label_counts):
            percent = label_counts[label] / valid * 100
            print(f" {label:.6f} : {percent:.2f}%")

    if valid:
        print("\nBucketed distribution (0.01 bins):")
        for bucket in sorted(bucket_counts):
            percent = bucket_counts[bucket] / valid * 100
            print(f" {bucket:.2f}-{bucket + 0.01:.2f} : {percent:.2f}%")
        print("\nAverage piece count:", round(piece_count_total / valid, 2))

    print("\nDuplicates:", duplicates)
    print("Broken FEN:", bad_fen)
    print("Bad labels:", bad_label)
    print("Decode errors:", decode_errors)
    print("Ctrl-Z markers:", ctrlz)

    if first_errors:
        print("\nFirst invalid records:")
        for kind, line_number, preview in first_errors:
            print(f" {kind} at line {line_number:,}: {preview!r}")
    print(f"\nFinished in {time.time() - start:.1f}s")

    return 1 if bad_fen or bad_label or decode_errors or ctrlz else 0


if __name__ == "__main__":
    raise SystemExit(main())
