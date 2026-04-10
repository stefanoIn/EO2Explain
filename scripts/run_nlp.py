#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(".")
    transformer = Path("nlp/transformer/transform_payload.py")
    ontology_populator = Path("nlp/ontology/populate_ontology.py")
    report_generator = Path("nlp/generator/report_generator.py")

    commands = [
        [sys.executable, str(transformer)],
        [sys.executable, str(ontology_populator)],
        [sys.executable, str(report_generator)],
    ]

    for command in commands:
        result = subprocess.call(command, cwd=root)
        if result != 0:
            return result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
