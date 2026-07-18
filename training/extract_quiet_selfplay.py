# extract_quiet_selfplay.py
# converts block selfplay logs into high-quality NNUE training data

import glob
import math
import random
import json
import os


# =========================
# Config loader
# =========================

def load_config(path="config.json"):
    if not os.path.exists(path):
        return {}

    with open(path, "r") as f:
        return json.load(f)


# =========================
# Score → probability
# =========================

def score_to_prob(cp):
    return 1.0 / (1.0 + math.exp(-cp / 400.0))


# =========================
# Detect captures
# =========================

def is_capture(move):
    return "x" in move


# =========================
# Count pieces on board
# =========================

def piece_count(fen):
    board = fen.split()[0]
    return sum(1 for c in board if c.isalpha())


# =========================
# Convert one file
# =========================

def convert_file(input_path, draw_drop_rate, min_ply, max_abs_score, min_pieces):

    output_path = input_path.replace(".txt", "_quiet.txt")

    fen = None
    move = None
    score = None
    ply = None

    written = 0
    seen = set()   # duplicate detection

    with open(input_path, "r") as fin, open(output_path, "w") as fout:

        for line in fin:

            line = line.strip()

            if line.startswith("fen "):
                fen = line[4:].strip()

            elif line.startswith("move "):
                move = line[5:].strip()

            elif line.startswith("score "):
                try:
                    score = int(line.split()[1])
                except:
                    score = None

            elif line.startswith("ply "):
                try:
                    ply = int(line.split()[1])
                except:
                    ply = None

            elif line == "e":

                if fen and move and score is not None and ply is not None:

                    # ------------------------
                    # Filters
                    # ------------------------

                    if ply < min_ply:
                        pass

                    elif abs(score) > max_abs_score:
                        pass

                    elif is_capture(move):
                        pass

                    elif piece_count(fen) < min_pieces:
                        pass

                    else:

                        fen4 = " ".join(fen.split()[:4])

                        # duplicate removal
                        if fen4 in seen:
                            pass
                        else:
                            seen.add(fen4)

                            prob = score_to_prob(score)

                            # draw reduction
                            if 0.45 < prob < 0.55:
                                if random.random() < draw_drop_rate:
                                    pass
                                else:
                                    fout.write(f"{fen4} | {prob:.6f}\n")
                                    written += 1
                            else:
                                fout.write(f"{fen4} | {prob:.6f}\n")
                                written += 1

                fen = None
                move = None
                score = None
                ply = None

    print(f"{input_path} → {written} positions")

    return written


# =========================
# Main
# =========================

def main():

    config = load_config()

    # reproducibility
    seed = config.get("seed", 42)
    random.seed(seed)

    # configurable filters
    draw_drop_rate = config.get("draw_drop_rate", 0.30)

    min_ply = config.get("quiet_min_ply", 10)
    max_abs_score = config.get("quiet_max_score", 3000)
    min_pieces = config.get("quiet_min_pieces", 6)

    files = sorted(glob.glob("*_plain.txt"))

    print("files found:", len(files))
    print("seed:", seed)
    print("draw_drop_rate:", draw_drop_rate)

    total = 0

    for f in files:

        n = convert_file(
            f,
            draw_drop_rate,
            min_ply,
            max_abs_score,
            min_pieces
        )

        total += n

    print("\nTOTAL POSITIONS:", total)


if __name__ == "__main__":
    main()