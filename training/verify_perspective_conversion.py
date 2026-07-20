# verify_perspective_conversion.py
# jasper sinclair

import argparse
from itertools import zip_longest
import math
import time


PERSPECTIVES = ("side_to_move", "white")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compare a converted corpus with its source record by record."
    )
    parser.add_argument("--source", required=True)
    parser.add_argument("--converted", required=True)
    parser.add_argument(
        "--source-perspective", choices=PERSPECTIVES, required=True
    )
    parser.add_argument(
        "--target-perspective", choices=PERSPECTIVES, required=True
    )
    parser.add_argument("--progress-every", type=int, default=5_000_000)
    return parser.parse_args()


def parse_record(raw, line_number, description):
    try:
        fen_part, label_part = raw.rstrip(b"\r\n").rsplit(b"|", 1)
        fields = fen_part.split()
        side = fields[1]
        label = float(label_part.strip())
    except (IndexError, ValueError) as error:
        raise ValueError(
            f"invalid {description} record at line {line_number:,}"
        ) from error

    if side not in (b"w", b"b") or not math.isfinite(label):
        raise ValueError(
            f"invalid {description} record at line {line_number:,}"
        )
    return fen_part.rstrip(), side, label


def main():
    args = parse_args()
    missing = object()
    records = 0
    transformed = 0
    started = time.monotonic()

    with open(args.source, "rb", buffering=8 * 1024 * 1024) as source, open(
        args.converted, "rb", buffering=8 * 1024 * 1024
    ) as converted:
        for records, (source_raw, converted_raw) in enumerate(
            zip_longest(source, converted, fillvalue=missing), 1
        ):
            if source_raw is missing or converted_raw is missing:
                raise ValueError(f"record-count mismatch at line {records:,}")

            source_fen, source_side, source_label = parse_record(
                source_raw, records, "source"
            )
            converted_fen, converted_side, converted_label = parse_record(
                converted_raw, records, "converted"
            )

            if source_fen != converted_fen or source_side != converted_side:
                raise ValueError(f"FEN mismatch at line {records:,}")

            should_transform = (
                args.source_perspective != args.target_perspective
                and source_side == b"b"
            )
            expected = 1.0 - source_label if should_transform else source_label
            expected = round(expected, 6)
            if not math.isclose(
                converted_label, expected, rel_tol=0.0, abs_tol=5e-7
            ):
                raise ValueError(
                    f"label mismatch at line {records:,}: "
                    f"expected {expected:.6f}, found {converted_label:.6f}"
                )

            transformed += int(should_transform)

            if args.progress_every and records % args.progress_every == 0:
                elapsed = max(time.monotonic() - started, 1e-9)
                print(
                    f"{records:,} records verified | "
                    f"{records / elapsed:,.0f} records/s",
                    flush=True,
                )

    print("Perspective conversion verified.")
    print(f"Records: {records:,}")
    print(f"Transformed Black-to-move records: {transformed:,}")


if __name__ == "__main__":
    main()
