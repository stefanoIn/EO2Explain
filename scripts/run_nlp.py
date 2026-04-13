#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    root = PROJECT_ROOT
    transformer = PROJECT_ROOT / "nlp/transformer/transform_payload.py"
    ontology_populator = PROJECT_ROOT / "nlp/ontology/populate_ontology.py"
    ontology_validator = PROJECT_ROOT / "nlp/ontology/validate_ontology.py"
    ontology_query = PROJECT_ROOT / "nlp/ontology/query_ontology.py"
    report_generator = PROJECT_ROOT / "nlp/generator/report_generator.py"

    commands = [
        [sys.executable, str(transformer)],
        [sys.executable, str(ontology_populator)],
        [sys.executable, str(ontology_validator)],
        [sys.executable, str(ontology_query)],
        [sys.executable, str(report_generator)],
    ]

    for command in commands:
        result = subprocess.call(command, cwd=root)
        if result != 0:
            return result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
