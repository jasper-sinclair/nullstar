# verify_corpus_manifest.py
# jasper sinclair

import hashlib
import json
import os
from pathlib import Path


def load_json(path):
    with open(path, "r", encoding="utf-8") as source:
        return json.load(source)


def resolved(path):
    return os.path.normcase(os.path.abspath(path))


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb", buffering=8 * 1024 * 1024) as source:
        while block := source.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def main():
    config_path = os.environ.get("NULLSTAR_TRAINING_CONFIG", "config.json")
    config = load_json(config_path) if os.path.exists(config_path) else {}
    corpus_path = Path(config.get("raw_training_txt", "training.txt")).resolve()
    configured_manifest = config.get("corpus_manifest")
    manifest_path = Path(
        configured_manifest or str(corpus_path) + ".manifest.json"
    ).resolve()
    required = bool(config.get("require_corpus_manifest", False))

    print("Corpus:", corpus_path)
    print("Manifest:", manifest_path)

    if not corpus_path.is_file():
        raise SystemExit(f"Corpus not found: {corpus_path}")

    if not manifest_path.is_file():
        if required or configured_manifest:
            raise SystemExit(f"Required corpus manifest not found: {manifest_path}")
        print("No corpus manifest found; perspective provenance was not verified.")
        return

    manifest = load_json(manifest_path)
    if manifest.get("kind") != "nullstar-nnue-text-corpus":
        raise SystemExit("Unrecognized corpus manifest kind")

    manifest_corpus = manifest.get("path")
    if manifest_corpus and resolved(manifest_corpus) != resolved(corpus_path):
        raise SystemExit(
            f"Manifest describes a different corpus: {manifest_corpus}"
        )

    expected_perspective = config.get("label_perspective", "side_to_move")
    actual_perspective = manifest.get("label_perspective")
    if actual_perspective != expected_perspective:
        raise SystemExit(
            "Label-perspective mismatch: "
            f"config={expected_perspective!r}, manifest={actual_perspective!r}"
        )

    actual_size = corpus_path.stat().st_size
    expected_size = manifest.get("bytes")
    if expected_size != actual_size:
        raise SystemExit(
            f"Corpus-size mismatch: manifest={expected_size}, file={actual_size}"
        )

    if config.get("verify_corpus_sha256", False):
        actual_hash = sha256(corpus_path)
        expected_hash = manifest.get("sha256")
        if actual_hash != expected_hash:
            raise SystemExit(
                f"Corpus SHA-256 mismatch: manifest={expected_hash}, file={actual_hash}"
            )
        print("SHA-256:", actual_hash)

    print("Perspective:", actual_perspective)
    print("Records:", f"{manifest.get('records', 0):,}")
    print("Corpus manifest is consistent.")


if __name__ == "__main__":
    main()
