# Nullstar NNUE networks

This directory contains quantized NNUE networks selected for public Nullstar
releases. Training checkpoints, datasets, and intermediate epoch exports remain
development artifacts and are not stored here.

Nullstar embeds its selected network in `src/net.cpp`. The files in this
directory support reproducibility and verification; they are not required
beside a finished engine executable.

## Nullstar 027 network

| Property | Value |
| --- | --- |
| File | `network_stm_base_epoch_29.bin` |
| Network ID | `stm-base-epoch-29` |
| Architecture | 768 inputs, 256 hidden neurons |
| Training epoch | 29 |
| Validation loss | `0.413940` |
| Bytes | 394,754 |
| SHA-256 | `9711CF740BA0C564B62FB41C93CDD0DD9E41FD2960DDC54E8D627C5339A55FCD` |
| First public release | Nullstar 027 |

The network was selected from a completed 30-epoch side-to-move training run.
It uses Nullstar's explicit side-to-move and opponent feature ordering.

Verify the published file from the repository root:

```powershell
Get-FileHash .\nets\network_stm_base_epoch_29.bin -Algorithm SHA256
```

After building `tools/embed_file`, regenerate the embedded source with:

```powershell
.\build\tools\embed_file.exe `
  .\nets\network_stm_base_epoch_29.bin `
  .\src\net.cpp
```

See [NETWORK.md](../docs/NETWORK.md), [EMBEDDING.md](../docs/EMBEDDING.md),
and [TRAINING.md](../docs/TRAINING.md) for architecture, quantization,
embedding, provenance, and training details.

The selected network was trained by Jasper Sinclair and is distributed with
Nullstar under `GPL-3.0-only`.
