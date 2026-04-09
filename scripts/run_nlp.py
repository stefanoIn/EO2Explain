#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    transformer = root / "nlp" / "transformer" / "transform_payload.py"
    command = [sys.executable, str(transformer)]
    return subprocess.call(command, cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
