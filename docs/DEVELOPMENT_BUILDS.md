# Nullstar development builds

This ledger separates the sequential development build from the NNUE
training epoch. The machine-readable source is DEVELOPMENT_BUILDS.json;
BUILD_INFO.json records the currently prepared source tree.

| Build | Change | Network | Epoch | Network SHA-256 | Playing-equivalent | Test | Summary |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| 018 | network | stm-base-epoch-14 | 14 | 8890EE63235B... | - | 2980 Elo; 10000 games; 68.93% | Epoch 14 STM network candidate; completed the 10,000-game reference gauntlet. |
| 019 | network | stm-base-epoch-18 | 18 | 267EC56988AB... | - | - | Epoch 18 STM network candidate. |
| 020 | documentation | stm-base-epoch-18 | 18 | 267EC56988AB... | 019 | - | Document the historical Kobra nnue-probe relationship and Nullstar's independent current NNUE implementation. |
| 021 | network | stm-base-epoch-19 | 19 | 1B0BA8AB6BEA... | - | - | Epoch 19 STM network candidate selected after the completed 20-epoch training run. |

## Preparing the next build

From the repository root, run:

```powershell
.\scripts\prepare_dev_build.ps1 `
  -NetworkFile "C:\path\to\network_stm_base_epoch_20.bin" `
  -Summary "Epoch 20 STM candidate" `
  -ValidationLoss 0.415064
```

The script chooses the next consecutive build number, validates and embeds
the network, updates the UCI version, and records exact SHA-256 hashes. Omit
-NetworkFile for a source, documentation, or tooling-only build; the current
network identity will be retained.

After compiling and verifying the binaries, copy the repository to the
suggested numbered snapshot directory printed by the script.

