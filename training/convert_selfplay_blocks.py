# convert_selfplay_blocks_batch.py

import glob
import math
import json
import os


# =========================
# Config loader
# =========================

def load_config(path="config.json"):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


# =========================
# Probability helpers
# =========================

def result_to_prob(r):
    r = int(r)

    if r == 1:
        return 1.0
    elif r == 0:
        return 0.5
    elif r == -1:
        return 0.0

    return None


def score_to_prob(score_cp):
    score_cp = max(-MAX_CP, min(MAX_CP, score_cp))
    return 1.0 / (1.0 + math.exp(-score_cp / SCORE_SCALING))


# =========================
# Convert one file
# =========================

def convert_file(input_path):

    output_path = input_path.replace("_plain.txt", "_training.txt")

    fen = None
    score = None
    result = None
    ply = None

    written = 0
    skipped_ply = 0
    skipped_score = 0

    with open(input_path, "r") as fin, open(output_path, "w") as fout:

        for line in fin:

            line = line.strip()

            if line.startswith("fen "):
                fen = line[4:].strip()

            elif line.startswith("score "):
                try:
                    score = int(line.split()[1])
                except:
                    score = None

            elif line.startswith("result "):
                result = line.split()[1]

            elif line.startswith("ply "):
                try:
                    ply = int(line.split()[1])
                except:
                    ply = None

            elif line == "e":

                if fen and ply is not None:

                    # filter opening noise
                    if ply < MIN_PLY:
                        skipped_ply += 1
                        fen = score = result = ply = None
                        continue

                    parts = fen.split()
                    stm = parts[1]

                    prob = None

                    if score is not None:

                        # filter extreme scores
                        if abs(score) > MAX_SCORE:
                            skipped_score += 1
                            fen = score = result = ply = None
                            continue

                        # convert to white perspective
                        if stm == "b":
                            score_adj = -score
                        else:
                            score_adj = score

                        prob = score_to_prob(score_adj)

                    elif result is not None:

                        prob = result_to_prob(result)

                    if prob is not None:

                        fen4 = " ".join(parts[:4])
                        fout.write(f"{fen4} | {prob:.6f}\n")
                        written += 1

                fen = None
                score = None
                result = None
                ply = None

    print("skipped ply <", MIN_PLY, ":", skipped_ply)
    print("skipped abs(score) >", MAX_SCORE, ":", skipped_score)

    return output_path, written


# =========================
# Main
# =========================

def main():

    global MAX_CP, MIN_PLY, MAX_SCORE, SCORE_SCALING

    config = load_config()

    SCORE_SCALING = config.get("sf_score_scaling", 400.0)
    MAX_CP = config.get("sf_max_cp", 2000)
    MIN_PLY = config.get("sf_min_ply", 8)
    MAX_SCORE = config.get("sf_max_score", 2000)

    print("Score scaling:", SCORE_SCALING)
    print("MAX_CP:", MAX_CP)
    print("MIN_PLY:", MIN_PLY)
    print("MAX_SCORE:", MAX_SCORE)

    files = sorted(glob.glob("*_plain.txt"))

    print("files found:", len(files))

    total = 0

    for f in files:

        print("processing:", f)

        output_path, n = convert_file(f)

        print("written:", n, "→", output_path)

        total += n

    print("\nTOTAL POSITIONS:", total)


if __name__ == "__main__":
    main()