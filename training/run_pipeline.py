# run_pipeline.py
# jasper sinclair

import json
import os
import subprocess
import sys
import time

CONFIG_ENV = "NULLSTAR_TRAINING_CONFIG"


def load_config(path):
    with open(path, "r", encoding="utf-8") as source:
        return json.load(source)


def build_pipeline(config):
    pipeline = [
        "verify_corpus_manifest.py",
        "verify_training_txt.py",
    ]
    if config.get("shuffle_training", True):
        pipeline.append("shuffle_training_txt.py")
    pipeline.extend([
        "convert_to_sparse.py",
        "verify_sparse_structure.py",
        "verify_sparse_features.py",
        "train.py",
    ])
    return pipeline


def prepare_directories(config):
    for key in (
        "training_file",
        "shuffle_output",
        "checkpoint_path",
        "mid_checkpoint_path",
        "best_model_path",
        "export_path",
        "log_path",
    ):
        path = config.get(key)
        if path:
            parent = os.path.dirname(os.path.abspath(path))
            os.makedirs(parent, exist_ok=True)


def run_step(script, environment):

    print("\n==============================")
    print("Running:", script)
    print("==============================\n")

    start = time.time()

    result = subprocess.run(
        [sys.executable, script],
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=environment,
    )

    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"\n❌ {script} FAILED")
        sys.exit(result.returncode)

    print(f"\n✅ {script} completed in {elapsed:.1f}s")


def main():
    config_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.environ.get(CONFIG_ENV, "config.json")
    )
    config_path = os.path.abspath(config_path)
    config = load_config(config_path)
    prepare_directories(config)
    environment = os.environ.copy()
    environment[CONFIG_ENV] = config_path

    print("Configuration:", config_path)
    print("Shuffle training data:", config.get("shuffle_training", True))

    for script in build_pipeline(config):
        run_step(script, environment)

    print("\n==============================")
    print("PIPELINE COMPLETE")
    print("==============================\n")


if __name__ == "__main__":
    main()
