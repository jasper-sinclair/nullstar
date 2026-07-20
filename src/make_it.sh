#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

mode="${1:-all}"
jobs="${JOBS:-$(nproc)}"

case "$mode" in
  all)
    make -j"$jobs" binaries
    ;;
  nonpgo)
    make -j"$jobs" nonpgo
    ;;
  pgo)
    make -j"$jobs" pgo
    ;;
  native|avx2|pgo-native|pgo-avx2)
    make -j"$jobs" "$mode"
    ;;
  clean)
    make distclean
    ;;
  *)
    echo "Usage: $0 [all|nonpgo|pgo|native|avx2|pgo-native|pgo-avx2|clean]" >&2
    exit 2
    ;;
esac

