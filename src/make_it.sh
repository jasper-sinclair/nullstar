#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

mode="${1:-all}"
jobs="${JOBS:-$(nproc)}"

if command -v make >/dev/null 2>&1; then
  make_command="make"
elif command -v mingw32-make >/dev/null 2>&1; then
  make_command="mingw32-make"
else
  echo "Neither make nor mingw32-make is available." >&2
  exit 1
fi

case "$mode" in
  all)
    "$make_command" -j"$jobs" binaries
    ;;
  nonpgo)
    "$make_command" -j"$jobs" nonpgo
    ;;
  pgo)
    "$make_command" -j"$jobs" pgo
    ;;
  native|avx2|pgo-native|pgo-avx2)
    "$make_command" -j"$jobs" "$mode"
    ;;
  clean)
    "$make_command" distclean
    ;;
  *)
    echo "Usage: $0 [all|nonpgo|pgo|native|avx2|pgo-native|pgo-avx2|clean]" >&2
    exit 2
    ;;
esac

