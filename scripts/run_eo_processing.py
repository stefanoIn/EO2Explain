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
            "--figure-event",
            "Emilia",
            "--figure-out",
            "eo_processing/flood/Emilia_flood_report_figure.png",
        ],
        [
            sys.executable,
            "eo_processing/wildfire/wildfire_indicators.py",
            "--figure-event",
            "Turkey",
            "--figure-out",
            "eo_processing/wildfire/Turkey_wildfire_report_figure.png",
        ],
    ]

    for command in commands:
        result = subprocess.call(command, cwd=project_root)
        if result != 0:
            return result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
