# split_training_txt.py
# jasper sinclair
#
# Split large NNUE training text files into smaller chunks.
#
# Input format:
#     FEN | result
#
# Example output:
#     dataset_part_0001.txt
#     dataset_part_0002.txt
#     dataset_part_0003.txt
#
# Designed for very large datasets (100M+ lines)

import sys
import os


def split_file(input_path, lines_per_chunk):

    base = os.path.splitext(os.path.basename(input_path))[0]

    part = 1
    written = 0

    fout = None

    with open(input_path, "r", buffering=1024*1024) as fin:

        for i, line in enumerate(fin, 1):

            if written == 0:
                output_name = f"{base}_part_{part:04d}.txt"
                fout = open(output_name, "w", buffering=1024*1024)
                print("writing:", output_name)

            fout.write(line)
            written += 1

            if written >= lines_per_chunk:
                fout.close()
                part += 1
                written = 0

        if fout:
            fout.close()

    print("\nDone.")
    print("Total parts:", part if written == 0 else part)


def main():

    if len(sys.argv) < 3:
        print("usage:")
        print("python split_training_txt.py input.txt lines_per_chunk")
        print("\nexample:")
        print("python split_training_txt.py 731704391_training.txt 10000000")
        return

    input_path = sys.argv[1]
    lines_per_chunk = int(sys.argv[2])

    print("Input file:", input_path)
    print("Lines per chunk:", f"{lines_per_chunk:,}")

    split_file(input_path, lines_per_chunk)


if __name__ == "__main__":
    main()