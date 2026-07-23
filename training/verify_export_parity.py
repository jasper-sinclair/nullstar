"""Verify that a quantized Nullstar network matches its PyTorch source model."""

import json
import os
from pathlib import Path

import numpy as np
import torch

from convert_to_sparse import BLACK, WHITE, parse_epd_line
from train import INPUT_SIZE, NNUE, build_features


CONFIG_ENV = "NULLSTAR_TRAINING_CONFIG"
INT16_MIN = np.iinfo(np.int16).min
INT16_MAX = np.iinfo(np.int16).max


def load_config():
    path = os.environ.get(CONFIG_ENV, "config.json")
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def quantize(values, scale):
    return np.clip(
        np.rint(np.asarray(values) * scale),
        INT16_MIN,
        INT16_MAX,
    ).astype(np.int16)


def load_state_dict(path):
    try:
        state = torch.load(path, map_location="cpu", weights_only=True)
    except TypeError:
        state = torch.load(path, map_location="cpu")
    if "model" in state:
        state = state["model"]
    return state


def decode_network(path, l1_size):
    payload = Path(path).read_bytes()
    expected_values = INPUT_SIZE * l1_size + l1_size + 2 * l1_size + 1
    expected_bytes = expected_values * 2
    if len(payload) != expected_bytes:
        raise ValueError(
            f"network size mismatch: expected {expected_bytes}, got {len(payload)}"
        )

    values = np.frombuffer(payload, dtype="<i2")
    cursor = 0

    input_weights = values[
        cursor:cursor + INPUT_SIZE * l1_size
    ].reshape(INPUT_SIZE, l1_size).T
    cursor += INPUT_SIZE * l1_size

    input_biases = values[cursor:cursor + l1_size]
    cursor += l1_size

    output_weights = values[cursor:cursor + 2 * l1_size].reshape(2, l1_size)
    cursor += 2 * l1_size

    output_bias = int(values[cursor])
    return input_weights, input_biases, output_weights, output_bias


def require_equal(description, actual, expected):
    if np.array_equal(actual, expected):
        return
    mismatches = np.flatnonzero(
        np.asarray(actual).reshape(-1) != np.asarray(expected).reshape(-1)
    )
    first = int(mismatches[0])
    raise ValueError(
        f"{description} differs at {len(mismatches):,} values; "
        f"first flattened index {first}"
    )


def select_verification_path(config):
    candidates = (
        config.get("verification_epd"),
        config.get("training_txt"),
        config.get("raw_training_txt"),
    )
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    raise FileNotFoundError(
        "no verification corpus exists; checked verification_epd, "
        "training_txt, and raw_training_txt"
    )


def load_positions(path, sample_count):
    stm_features = []
    nstm_features = []
    with open(path, encoding="utf-8", newline="") as source:
        for line in source:
            fen, _ = parse_epd_line(line)
            if fen is None:
                continue

            side = fen.split()[1]
            if side == "w":
                stm, nstm = WHITE, BLACK
            elif side == "b":
                stm, nstm = BLACK, WHITE
            else:
                continue

            stm_features.append(build_features(fen, stm))
            nstm_features.append(build_features(fen, nstm))
            if len(stm_features) >= sample_count:
                break

    if not stm_features:
        raise ValueError(f"no valid verification positions found in {path}")
    return np.stack(stm_features), np.stack(nstm_features)


def main():
    config = load_config()
    scale = int(config.get("scale", 128))
    l1_size = int(config.get("l1_size", 256))
    sample_count = int(config.get("export_parity_samples", 128))
    maximum_error = float(
        config.get("export_parity_max_logit_error", 0.25)
    )

    if scale <= 0:
        raise ValueError("scale must be positive")
    if sample_count <= 0:
        raise ValueError("export_parity_samples must be positive")

    model_path = config.get("best_model_path", "best_model.pt")
    network_path = config.get("export_path", "network.bin")
    verification_path = select_verification_path(config)

    model = NNUE(l1_size)
    model.load_state_dict(load_state_dict(model_path))
    model.eval()

    input_weights, input_biases, output_weights, output_bias = decode_network(
        network_path, l1_size
    )

    require_equal(
        "input weights",
        input_weights,
        quantize(model.fc1.weight.detach().cpu().numpy(), scale),
    )
    require_equal(
        "input biases",
        input_biases,
        quantize(model.fc1.bias.detach().cpu().numpy(), scale),
    )
    require_equal(
        "output weights",
        output_weights,
        quantize(
            model.fc2.weight.detach().cpu().numpy().reshape(2, l1_size),
            scale,
        ),
    )
    expected_output_bias = int(
        quantize(model.fc2.bias.detach().cpu().numpy(), scale)[0]
    )
    if output_bias != expected_output_bias:
        raise ValueError(
            f"output bias differs: {output_bias} != {expected_output_bias}"
        )

    x_stm, x_nstm = load_positions(verification_path, sample_count)
    with torch.no_grad():
        float_logits = model(
            torch.from_numpy(x_stm),
            torch.from_numpy(x_nstm),
        ).cpu().numpy()

    input_weights_64 = input_weights.astype(np.int64)
    input_biases_64 = input_biases.astype(np.int64)
    stm_acc = x_stm.astype(np.int64) @ input_weights_64.T + input_biases_64
    nstm_acc = x_nstm.astype(np.int64) @ input_weights_64.T + input_biases_64
    stm_activation = np.clip(stm_acc, 0, scale)
    nstm_activation = np.clip(nstm_acc, 0, scale)

    weighted = (
        (stm_activation * stm_activation)
        @ output_weights[0].astype(np.int64)
        + (nstm_activation * nstm_activation)
        @ output_weights[1].astype(np.int64)
        + output_bias * scale * scale
    )
    quantized_logits = weighted.astype(np.float64) / (scale ** 3)
    errors = np.abs(quantized_logits - float_logits)

    print("Model:", os.path.abspath(model_path))
    print("Network:", os.path.abspath(network_path))
    print("Verification corpus:", os.path.abspath(verification_path))
    print("Positions:", len(float_logits))
    print("Quantization scale:", scale)
    print("Mean logit error:", f"{errors.mean():.6f}")
    print("Maximum logit error:", f"{errors.max():.6f}")
    print("Maximum centipawn error:", f"{errors.max() * 400.0:.2f}")

    if errors.max() > maximum_error:
        raise ValueError(
            f"maximum logit error {errors.max():.6f} exceeds "
            f"configured limit {maximum_error:.6f}"
        )

    print("Export parity verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
