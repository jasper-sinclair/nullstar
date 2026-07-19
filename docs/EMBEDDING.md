# NNUE embedding tool

The `tools/embed_file/` utility converts a quantized `network.bin` into the
`src/net.cpp` byte array linked into Nullstar. The finished chess-engine
executable does not load an external network file.

Build with CMake from the repository root:

```powershell
cmake -S .\tools\embed_file -B .\build\embed_file
cmake --build .\build\embed_file --config Release
```

Alternatively, build directly with MinGW:

```powershell
New-Item -ItemType Directory -Force .\build\tools | Out-Null
g++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -static `
  .\tools\embed_file\embed_file.cpp `
  -o .\build\tools\embed_file.exe
```

Generate the engine source from a newly trained network:

```powershell
.\build\tools\embed_file.exe .\training\network.bin .\src\net.cpp
```

The input must match Nullstar's 768x256 signed-16-bit network layout. Nullstar
checks the embedded byte count at startup and exits if the layout is wrong.
