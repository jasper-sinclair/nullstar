# Building Nullstar

Nullstar's release builds use C++23 with MinGW and the latest available C++
language mode with MSVC. Final executables are written to the repository root;
objects and profile data remain isolated under `build/`.

## Visual Studio / MSVC

Build the normal x64 release from Visual Studio by opening
`src/nullstar.sln`, or from a developer shell:

```powershell
msbuild src\nullstar.sln /t:Rebuild /m /p:Configuration=Release /p:Platform=x64
```

Output: `nullstar_msvc_nonpgo.exe`.

For the profile-guided release, double-click `build_msvc_pgo.bat`, or run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_msvc_pgo.ps1
```

The script instruments Nullstar, trains it with the deterministic 32-position
benchmark, links the optimized executable, and verifies the benchmark
signature. Output: `nullstar_msvc_pgo.exe`.

## MinGW-w64

Run these commands from the `src` directory.

Normal LTO builds:

```sh
mingw32-make native
mingw32-make avx2
```

Outputs: `nullstar_mingw_native_nonpgo.exe` and
`nullstar_mingw_avx2_nonpgo.exe`.

PGO + LTO builds:

```sh
mingw32-make pgo-native
mingw32-make pgo-avx2
```

Outputs: `nullstar_mingw_native_pgo.exe` and
`nullstar_mingw_avx2_pgo.exe`.

`native` is tuned for the build machine. `avx2` targets the portable
x86-64-v3 baseline (AVX2, BMI2, and related instructions). The legacy `v3`
and `pgo-v3` target names remain aliases. PGO targets retrain from scratch so
stale profiles cannot leak into a release.
