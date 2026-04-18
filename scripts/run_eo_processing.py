#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    commands = [
        [
            sys.executable,
            "eo_processing/population/population_exposure.py",
        ],
        [
            sys.executable,
            "eo_processing/flood/flood_indicators.py",
            "--figure-all",
            "--figure-dir",
            "outputs/figures/flood",
        ],
        [
            sys.executable,
            "eo_processing/wildfire/wildfire_indicators.py",
            "--figure-all",
            "--figure-dir",
            "outputs/figures/wildfire",
        ],
    ]

    for command in commands:
        result = subprocess.call(command, cwd=project_root)
        if result != 0:
            return result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
