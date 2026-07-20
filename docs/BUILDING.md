# Building Nullstar

Nullstar's release builds use C++23 with MinGW and the latest available C++
language mode with MSVC. Final executables are written to `binaries/`; objects
and MinGW profile data remain isolated under `build/`.

## Visual Studio / MSVC

Build the normal x64 release from Visual Studio by opening
`src/nullstar.sln`, or from a developer shell:

```powershell
msbuild src\nullstar.sln /t:Rebuild /m /p:Configuration=Release /p:Platform=x64
```

Output: `binaries/nullstar_msvc_nonpgo.exe`.

For the profile-guided release, double-click
`scripts\build_msvc_pgo.bat`, or run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_msvc_pgo.ps1
```

The script instruments Nullstar, trains it with the deterministic 32-position
benchmark, links the optimized executable, and verifies the benchmark
signature. Output: `binaries/nullstar_msvc_pgo.exe`.

## MinGW-w64

Open an MSYS2 MinGW64 shell and run these commands from the `src` directory.
To build all four MinGW release binaries with one command:

```sh
./make_it.sh
```

The launcher also accepts `nonpgo`, `pgo`, `native`, `avx2`, `pgo-native`,
`pgo-avx2`, and `clean`. Set `JOBS` to override its default of using all
available logical processors.

Normal LTO builds:

```sh
make native
make avx2
```

Outputs: `binaries/nullstar_mingw_native_nonpgo.exe` and
`binaries/nullstar_mingw_avx2_nonpgo.exe`.

PGO + LTO builds:

```sh
make pgo-native
make pgo-avx2
```

Outputs: `binaries/nullstar_mingw_native_pgo.exe` and
`binaries/nullstar_mingw_avx2_pgo.exe`.

`native` is tuned for the build machine. `avx2` targets the portable
x86-64-v3 baseline (AVX2, BMI2, and related instructions). The legacy `v3`
and `pgo-v3` target names remain aliases. PGO targets retrain from scratch so
stale profiles cannot leak into a release.

## Embedded NNUE

`src/net.cpp` contains the default quantized network and is compiled by both
build systems. A separate `network.bin` is not needed to build or run Nullstar.
To replace the network, follow [`TRAINING.md`](TRAINING.md) and use the source
utility documented in [`EMBEDDING.md`](EMBEDDING.md); then rebuild every
release target.
