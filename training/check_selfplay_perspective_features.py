import json
import os


def load_config(path="config.json"):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)


def main():
    config = load_config()
    training_file = config.get("raw_training_txt", "training.txt")
    sample_limit = config.get("verify_sample_limit", 0)

    counts = {"w": 0, "b": 0}
    sums = {"w": 0.0, "b": 0.0}
    invalid = 0

    print("Checking self-play labels:", training_file)
    print("Expected perspective: side_to_move")

    with open(training_file, "r") as f:
        for line in f:
            if "|" not in line:
                invalid += 1
                continue

            fen_part, label_part = line.split("|", 1)
            fields = fen_part.split()

            try:
                side_to_move = fields[1]
                label = float(label_part.strip())
            except (IndexError, ValueError):
                invalid += 1
                continue

            if side_to_move not in counts or not 0.0 <= label <= 1.0:
                invalid += 1
                continue

            counts[side_to_move] += 1
            sums[side_to_move] += label

            if sample_limit and sum(counts.values()) >= sample_limit:
                break

    checked = sum(counts.values())
    print("Checked:", checked)
    print("Invalid:", invalid)

    for side in ("w", "b"):
        mean = sums[side] / counts[side] if counts[side] else 0.0
        print(f"{side}: count={counts[side]} mean_label={mean:.6f}")

    if invalid:
        raise SystemExit("Self-play data contains invalid records")

    if config.get("label_perspective", "side_to_move") != "side_to_move":
        raise SystemExit(
            "Nullstar self-play writes side-to-move labels; update label_perspective"
        )

    print("Self-play label structure is valid.")
    print(
        "Perspective meaning cannot be inferred statistically from FEN and label "
        "alone; sparse feature order is verified after conversion."
    )


if __name__ == "__main__":
    main()
