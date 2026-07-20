# run_pipeline.py
# jasper sinclair

import argparse
import codecs
import json
import locale
import os
import subprocess
import sys
import time
from datetime import datetime

CONFIG_ENV = "NULLSTAR_TRAINING_CONFIG"


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, value):
        for stream in self.streams:
            stream.write(value)
        return len(value)

    def flush(self):
        for stream in self.streams:
            stream.flush()

    def isatty(self):
        return False


def load_config(path):
    with open(path, "r", encoding="utf-8") as source:
        return json.load(source)


def pipeline_log_path(config):
    configured = config.get("pipeline_log_path")
    if configured:
        return os.path.abspath(configured)

    training_log = os.path.abspath(config.get("log_path", "training.log"))
    root, extension = os.path.splitext(training_log)
    return root + "_pipeline" + (extension or ".log")


def build_pipeline(config, start_at=None):
    pipeline = [
        ["verify_corpus_manifest.py"],
        ["verify_training_txt.py"],
    ]
    if config.get("shuffle_training", True):
        pipeline.append(["shuffle_training_txt.py"])
        if config.get("verify_shuffled_training", True):
            pipeline.append([
                "verify_training_txt.py",
                config.get("training_txt", "training_shuffled.txt"),
            ])
    pipeline.extend([
        ["convert_to_sparse.py"],
        ["verify_sparse_structure.py"],
        ["verify_sparse_features.py"],
        ["train.py"],
    ])
    if start_at:
        for index, command in enumerate(pipeline):
            if command[0] == start_at:
                return pipeline[index:]
        raise ValueError(f"pipeline step not found: {start_at}")
    return pipeline


def prepare_directories(config):
    for key in (
        "training_file",
        "offset_index_path",
        "shuffle_output",
        "checkpoint_path",
        "mid_checkpoint_path",
        "best_model_path",
        "export_path",
        "log_path",
        "pipeline_log_path",
    ):
        path = config.get(key)
        if path:
            parent = os.path.dirname(os.path.abspath(path))
            os.makedirs(parent, exist_ok=True)


def run_step(command, environment):
    display = " ".join(command)
    print("\n==============================")
    print("Running:", display)
    print("==============================\n")

    start = time.time()
    process = subprocess.Popen(
        [sys.executable, *command],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=environment,
    )

    encoding = environment.get(
        "PYTHONIOENCODING", locale.getpreferredencoding(False)
    ).split(":", 1)[0]
    decoder = codecs.getincrementaldecoder(encoding)(errors="replace")
    while True:
        chunk = process.stdout.read1(64 * 1024)
        if not chunk:
            break
        sys.stdout.write(decoder.decode(chunk))
        sys.stdout.flush()
    final_text = decoder.decode(b"", final=True)
    if final_text:
        sys.stdout.write(final_text)
        sys.stdout.flush()

    return_code = process.wait()
    elapsed = time.time() - start

    if return_code != 0:
        print(f"\nFAILED: {display} (exit code {return_code})")
        raise SystemExit(return_code)

    print(f"\nCompleted: {display} ({elapsed:.1f}s)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", nargs="?")
    parser.add_argument(
        "--start-at",
        choices=(
            "verify_corpus_manifest.py",
            "verify_training_txt.py",
            "shuffle_training_txt.py",
            "convert_to_sparse.py",
            "verify_sparse_structure.py",
            "verify_sparse_features.py",
            "train.py",
        ),
    )
    arguments = parser.parse_args()
    config_path = arguments.config or os.environ.get(CONFIG_ENV, "config.json")
    config_path = os.path.abspath(config_path)
    config = load_config(config_path)
    prepare_directories(config)
    transcript_path = pipeline_log_path(config)
    os.makedirs(os.path.dirname(transcript_path), exist_ok=True)

    environment = os.environ.copy()
    environment[CONFIG_ENV] = config_path
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUNBUFFERED"] = "1"
    environment["PYTHONFAULTHANDLER"] = "1"

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    with open(transcript_path, "a", encoding="utf-8", buffering=1) as transcript:
        sys.stdout = Tee(original_stdout, transcript)
        sys.stderr = Tee(original_stderr, transcript)
        try:
            print("\n" + "=" * 70)
            print("Pipeline started:", datetime.now().astimezone().isoformat())
            print("Configuration:", config_path)
            print("Pipeline log:", transcript_path)
            print("Shuffle training data:", config.get("shuffle_training", True))
            print("Starting step:", arguments.start_at or "beginning")

            for command in build_pipeline(config, arguments.start_at):
                run_step(command, environment)

            print("\n==============================")
            print("PIPELINE COMPLETE")
            print("==============================\n")
        finally:
            sys.stdout.flush()
            sys.stderr.flush()
            sys.stdout = original_stdout
            sys.stderr = original_stderr


if __name__ == "__main__":
    main()
