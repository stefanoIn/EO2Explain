#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_payloads(payload_dir: Path | str = "outputs/transformed") -> list[dict[str, Any]]:
    directory = Path(payload_dir)
    payloads = []
    for path in sorted(directory.glob("*.json")):
        if path.name == "index.json":
            continue
        payloads.append(json.loads(path.read_text(encoding="utf-8")))
    return payloads


if __name__ == "__main__":
    for payload in load_payloads():
        print(payload["event_id"])
