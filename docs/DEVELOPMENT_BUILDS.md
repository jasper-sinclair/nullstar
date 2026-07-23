# Nullstar development builds

This ledger separates the sequential development build from the NNUE
training epoch. The machine-readable source is DEVELOPMENT_BUILDS.json;
BUILD_INFO.json records the currently prepared source tree.

| Build | Change | Network | Epoch | Network SHA-256 | Playing-equivalent | Test | Summary |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| 018 | network | stm-base-epoch-14 | 14 | 8890EE63235B... | - | 2980 Elo; 10000 games; 68.93% | Epoch 14 STM network candidate; completed the 10,000-game reference gauntlet. |
| 019 | network | stm-base-epoch-18 | 18 | 267EC56988AB... | - | - | Epoch 18 STM network candidate. |
| 020 | documentation | stm-base-epoch-18 | 18 | 267EC56988AB... | 019 | - | Document the historical Kobra nnue-probe relationship and Nullstar's independent current NNUE implementation. |
| 021 | network | stm-base-epoch-19 | 19 | 1B0BA8AB6BEA... | - | 2994 Elo; 10000 games; 70.67% | Epoch 19 STM network candidate selected after the completed 20-epoch training run. |
| 022 | network | stm-base-epoch-29 | 29 | 9711CF740BA0... | - | - | Epoch 29 STM network candidate selected after the completed 30-epoch training run. |
| 023 | source | stm-base-epoch-29 | 29 | 9711CF740BA0... | - | 2995 Elo; 10000 games; 70.25% | Correct quiescence terminal detection when the transposition-table move is the only legal move. |
| 024 | source | stm-base-epoch-29 | 29 | 9711CF740BA0... | - | 3052 Elo; 10000 games; 76.06% | Restrict static-exchange recapture selection to attackers of the side to move. |
| 025 | source | stm-base-epoch-29 | 29 | 9711CF740BA0... | - | 3048 Elo; 10000 games; 75.64% | Evaluate direct and discovered checks using complete post-move occupancy. |
| 026 | source | stm-base-epoch-29 | 29 | 9711CF740BA0... | - | 3056 Elo; 10000 games; 76.22%; strong pool: 3022 Elo; 10240 games; 49.5% | Pack transposition-table entries into fully guarded 16-byte atomic slots. |
| 027 | source | stm-base-epoch-29 | 29 | 9711CF740BA0... | - | strong pool: 3081 Elo; 10240 games; 57.08% | Align quantized NNUE inference with the trainer and add export-parity regression checks. |

## Preparing the next build

From the repository root, run:

```powershell
.\scripts\prepare_dev_build.ps1 `
  -NetworkFile "C:\path\to\network_candidate.bin" `
  -NetworkId "stm-next-candidate" `
  -Summary "Next STM network candidate" `
  -ValidationLoss 0.400000
```

The script chooses the next consecutive build number, validates and embeds
the network, updates the UCI version, and records exact SHA-256 hashes. Omit
-NetworkFile for a source, documentation, or tooling-only build; the current
network identity will be retained.

After compiling and verifying the binaries, copy the repository to the
suggested numbered snapshot directory printed by the script.

