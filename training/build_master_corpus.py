# build_master_corpus.py
# jasper sinclair

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time


PERSPECTIVES = ("side_to_move", "white")
SCHEMA_VERSION = 1


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Build a strict, canonical NNUE text corpus while converting each "
            "source's labels to one target perspective."
        )
    )
    parser.add_argument(
        "--source",
        action="append",
        nargs=2,
        required=True,
        metavar=("PATH", "PERSPECTIVE"),
        help=(
            "Input file and its label perspective. Repeat for additional "
            "sources. PERSPECTIVE is side_to_move or white."
        ),
    )
    parser.add_argument("--output", required=True, help="New master corpus path")
    parser.add_argument(
        "--target-perspective",
        choices=PERSPECTIVES,
        default="side_to_move",
    )
    parser.add_argument(
        "--manifest",
        help="Manifest path; defaults to OUTPUT.manifest.json",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=5_000_000,
        help="Report progress after this many records; zero disables reports",
    )
    parser.add_argument(
        "--replace-incomplete",
        action="store_true",
        help="Restart by replacing OUTPUT.part; never replaces a completed output",
    )
    return parser.parse_args()


def resolved(path):
    return os.path.normcase(os.path.abspath(path))


def line_ending(raw):
    if raw.endswith(b"\r\n"):
        return raw[:-2], b"\r\n"
    if raw.endswith(b"\n") or raw.endswith(b"\r"):
        return raw[:-1], raw[-1:]
    return raw, b"\n"


def transformed_line(raw, source_perspective, target_perspective, line_number):
    body, ending = line_ending(raw)

    try:
        fen_part, label_part = body.rsplit(b"|", 1)
        fields = fen_part.split()
        side_to_move = fields[1]
        label = float(label_part.strip())
    except (IndexError, ValueError) as error:
        raise ValueError(f"invalid record at line {line_number:,}") from error

    if side_to_move not in (b"w", b"b"):
        raise ValueError(
            f"invalid side-to-move at line {line_number:,}: "
            f"{side_to_move!r}"
        )

    if not math.isfinite(label) or not 0.0 <= label <= 1.0:
        raise ValueError(
            f"invalid label at line {line_number:,}: {label_part.strip()!r}"
        )

    changed = source_perspective != target_perspective and side_to_move == b"b"
    if not changed and raw.endswith((b"\n", b"\r")):
        return raw, side_to_move, label, False

    output_label = 1.0 - label if changed else label
    output_label = min(1.0, max(0.0, output_label))
    output = (
        fen_part.rstrip()
        + b" | "
        + f"{output_label:.6f}".encode("ascii")
        + ending
    )
    return output, side_to_move, output_label, changed


def write_json_atomic(path, value):
    temporary = Path(str(path) + ".part")
    with temporary.open("w", encoding="utf-8", newline="\n") as destination:
        json.dump(value, destination, indent=2)
        destination.write("\n")
        destination.flush()
        os.fsync(destination.fileno())
    os.replace(temporary, path)


def build_source(source_path, source_perspective, target, destination, output_hash,
                 progress_every, total_records, start_time):
    source_hash = hashlib.sha256()
    source_size = os.path.getsize(source_path)
    records = 0
    white_records = 0
    black_records = 0
    transformed_records = 0
    input_bytes = 0
    output_bytes = 0

    print(f"Source: {source_path}")
    print(f"Source perspective: {source_perspective}")

    with open(source_path, "rb", buffering=8 * 1024 * 1024) as source:
        for records, raw in enumerate(source, 1):
            source_hash.update(raw)
            input_bytes += len(raw)

            output, side, _, changed = transformed_line(
                raw,
                source_perspective,
                target,
                records,
            )
            destination.write(output)
            output_hash.update(output)
            output_bytes += len(output)

            if side == b"w":
                white_records += 1
            else:
                black_records += 1
            transformed_records += int(changed)

            if progress_every and records % progress_every == 0:
                elapsed = max(time.monotonic() - start_time, 1e-9)
                percent = 100.0 * input_bytes / source_size
                rate = (total_records + records) / elapsed
                print(
                    f"  {records:,} records | {percent:6.2f}% | "
                    f"{rate:,.0f} records/s",
                    flush=True,
                )

    if records == 0:
        raise ValueError(f"source is empty: {source_path}")

    return {
        "path": str(Path(source_path).resolve()),
        "label_perspective": source_perspective,
        "records": records,
        "white_to_move_records": white_records,
        "black_to_move_records": black_records,
        "transformed_records": transformed_records,
        "bytes": input_bytes,
        "sha256": source_hash.hexdigest(),
    }, output_bytes


def main():
    args = parse_args()
    output_path = Path(args.output).resolve()
    manifest_path = Path(args.manifest).resolve() if args.manifest else Path(
        str(output_path) + ".manifest.json"
    )
    temporary_path = Path(str(output_path) + ".part")

    sources = []
    for path_text, perspective in args.source:
        if perspective not in PERSPECTIVES:
            raise SystemExit(
                f"Invalid perspective {perspective!r}; choose from {PERSPECTIVES}"
            )
        path = Path(path_text).resolve()
        if not path.is_file():
            raise SystemExit(f"Source not found: {path}")
        sources.append((path, perspective))

    forbidden = {resolved(path) for path, _ in sources}
    if resolved(output_path) in forbidden or resolved(manifest_path) in forbidden:
        raise SystemExit("Output and manifest must not overwrite a source")
    if output_path.exists():
        raise SystemExit(f"Output already exists: {output_path}")
    if manifest_path.exists():
        raise SystemExit(f"Manifest already exists: {manifest_path}")
    if temporary_path.exists() and not args.replace_incomplete:
        raise SystemExit(
            f"Incomplete output already exists: {temporary_path}\n"
            "Inspect it or pass --replace-incomplete to restart safely."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Output: {output_path}")
    print(f"Target perspective: {args.target_perspective}")
    print(f"Manifest: {manifest_path}")

    started_utc = dt.datetime.now(dt.timezone.utc)
    started = time.monotonic()
    output_hash = hashlib.sha256()
    source_manifests = []
    total_records = 0
    total_output_bytes = 0

    try:
        temporary_mode = "wb" if args.replace_incomplete else "xb"
        with temporary_path.open(
            temporary_mode, buffering=8 * 1024 * 1024
        ) as destination:
            for source_path, source_perspective in sources:
                source_manifest, output_bytes = build_source(
                    source_path,
                    source_perspective,
                    args.target_perspective,
                    destination,
                    output_hash,
                    args.progress_every,
                    total_records,
                    started,
                )
                source_manifests.append(source_manifest)
                total_records += source_manifest["records"]
                total_output_bytes += output_bytes

            destination.flush()
            os.fsync(destination.fileno())

        os.replace(temporary_path, output_path)
    except BaseException:
        print(f"Incomplete output retained as: {temporary_path}", file=sys.stderr)
        raise

    finished_utc = dt.datetime.now(dt.timezone.utc)
    elapsed = time.monotonic() - started
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "kind": "nullstar-nnue-text-corpus",
        "path": str(output_path),
        "record_format": "FEN | probability",
        "label_perspective": args.target_perspective,
        "records": total_records,
        "bytes": total_output_bytes,
        "sha256": output_hash.hexdigest(),
        "created_utc": finished_utc.isoformat(),
        "elapsed_seconds": round(elapsed, 3),
        "sources": source_manifests,
    }
    write_json_atomic(manifest_path, manifest)

    print("\nMaster corpus complete")
    print(f"Records: {total_records:,}")
    print(f"Bytes: {total_output_bytes:,}")
    print(f"SHA-256: {manifest['sha256']}")
    print(f"Elapsed: {elapsed:.1f} seconds")


if __name__ == "__main__":
    main()
