# run_pipeline.py
# jasper sinclair

import subprocess
import sys
import time

pipeline = [
    "check_selfplay_perspective_features.py",
    "shuffle_training_txt.py",
    "convert_to_sparse.py",
    "verify_sparse_structure.py",
    "train.py",
]

def run_step(script):

    print("\n==============================")
    print("Running:", script)
    print("==============================\n")

    start = time.time()

    result = subprocess.run(
        [sys.executable, script],
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\n❌ {script} FAILED")
        sys.exit(result.returncode)

    print(f"\n✅ {script} completed in {elapsed:.1f}s")


def main():

    for script in pipeline:
        run_step(script)

    print("\n==============================")
    print("PIPELINE COMPLETE")
    print("==============================\n")


if __name__ == "__main__":
    main()
