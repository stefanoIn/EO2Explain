#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/mas"

if ! command -v jason >/dev/null 2>&1; then
    echo "The 'jason' CLI was not found in PATH." >&2
    echo "Run this script after installing Jason CLI, or invoke 'jason eo.mas2j' from EO2Explain/mas." >&2
    exit 1
fi

jason eo.mas2j
