# NNUE embedding and development-build preparation

The `tools/embed_file.cpp` utility converts a quantized `network.bin` into the
`src/net.cpp` byte array linked into Nullstar. The finished chess-engine
executable does not load an external network file.

For development candidates, use `scripts/prepare_dev_build.ps1` instead of
calling the embedding tool directly. It selects the next consecutive build,
validates and hashes the network, regenerates `src/net.cpp`, updates Nullstar's
UCI identity, and records the relationship in `BUILD_INFO.json` and the
development-build ledger.

If the repository-local embedding executable is absent or older than its
source, the preparation script builds it automatically with the installed
MSYS2 MinGW compiler. An explicit alternative can be supplied with
`-EmbedTool` when required.

```powershell
.\scripts\prepare_dev_build.ps1 `
  -NetworkFile "C:\path\to\network_stm_base_epoch_20.bin" `
  -Summary "Epoch 20 STM candidate" `
  -ValidationLoss 0.415064
```

See [`DEVELOPMENT_BUILDS.md`](DEVELOPMENT_BUILDS.md) for the complete workflow.

## Building the embedding utility manually

Build with CMake from the repository root:

```powershell
cmake -S .\tools -B .\build\embed_file
cmake --build .\build\embed_file --config Release
```

Alternatively, build directly with MinGW:

```powershell
New-Item -ItemType Directory -Force .\build\tools | Out-Null
g++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -static `
  .\tools\embed_file.cpp `
  -o .\build\tools\embed_file.exe
```

For low-level manual use, generate the engine source directly:

```powershell
.\build\tools\embed_file.exe .\training\network.bin .\src\net.cpp
```

The input must match Nullstar's 768x256 signed-16-bit network layout. Nullstar
checks the embedded byte count at startup and exits if the layout is wrong.
