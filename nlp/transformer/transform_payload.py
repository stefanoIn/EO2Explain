#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def decode_value(node: Any) -> Any:
    if isinstance(node, list):
        return [decode_value(item) for item in node]
    if isinstance(node, (str, int, float, bool)) or node is None:
        return node
    if not isinstance(node, dict):
        raise TypeError(f"Unsupported node type: {type(node)!r}")

    functor = node.get("functor")
    terms = node.get("terms", [])

    if not terms:
        return functor

    return {
        "functor": functor,
        "terms": [decode_value(term) for term in terms],
    }


def parse_field_node(node: dict[str, Any]) -> tuple[str, Any]:
    key = node["functor"]
    values = [decode_value(term) for term in node.get("terms", [])]

    if key in {"country", "region"} and len(values) == 2:
        return key, {"id": values[0], "name": values[1]}

    if len(values) == 1:
        return key, values[0]

    return key, values


def parse_frame(node: dict[str, Any], expected_functor: str) -> dict[str, Any]:
    if node.get("functor") != expected_functor:
        raise ValueError(
            f"Expected frame functor '{expected_functor}', found '{node.get('functor')}'"
        )

    result: dict[str, Any] = {}
    for child in node.get("terms", []):
        key, value = parse_field_node(child)
        result[key] = value
    return result


def parse_debug_text(node: dict[str, Any]) -> dict[str, Any]:
    return parse_frame(node, "debug_text")


def parse_clarification_trace(node: dict[str, Any]) -> dict[str, Any]:
    if node.get("functor") != "clarification_trace":
        raise ValueError(
            f"Expected clarification_trace, found '{node.get('functor')}'"
        )

    terms = [decode_value(term) for term in node.get("terms", [])]
    if len(terms) != 4:
        raise ValueError("clarification_trace must have exactly 4 terms")

    return {
        "clarification_status": terms[0],
        "primary_limitation": terms[1],
        "strongest_evidence": terms[2],
        "alternative_claim": terms[3],
    }


def parse_explanation_trace(node: dict[str, Any]) -> dict[str, Any]:
    if node.get("functor") != "explanation_trace":
        raise ValueError(f"Expected explanation_trace, found '{node.get('functor')}'")

    terms = node.get("terms", [])
    if len(terms) != 6:
        raise ValueError("explanation_trace must have exactly 6 terms")

    return {
        "source_agent": decode_value(terms[0]),
        "rule_label": decode_value(terms[1]),
        "claim_label": decode_value(terms[2]),
        "evidence_items": decode_value(terms[3]),
        "caveat_items": decode_value(terms[4]),
        "clarification_trace": parse_clarification_trace(terms[5]),
    }


def transform_semantic_explanation(raw: dict[str, Any], source_name: str) -> dict[str, Any]:
    if raw.get("functor") != "semantic_explanation":
        raise ValueError(
            f"Expected top-level semantic_explanation, found '{raw.get('functor')}'"
        )

    terms = raw.get("terms", [])
    if len(terms) != 9:
        raise ValueError("semantic_explanation must have exactly 9 top-level terms")

    event_id = decode_value(terms[0])
    event_frame = parse_frame(terms[1], "event_frame")
    assessment = parse_frame(terms[2], "assessment_frame")
    evidence = parse_frame(terms[3], "evidence_frame")
    clarification = parse_frame(terms[4], "clarification_frame")
    provenance = parse_frame(terms[5], "provenance_frame")
    headline = parse_frame(terms[6], "headline_frame")
    debug = parse_debug_text(terms[7])
    trace = parse_explanation_trace(terms[8])

    return {
        "event_id": event_id,
        "event": event_frame,
        "assessment": assessment,
        "evidence": evidence,
        "clarification": clarification,
        "provenance": provenance,
        "headline": headline,
        "debug": debug,
        "trace": trace,
        "metadata": {
            "source_raw_file": source_name,
            "source_functor": raw.get("functor"),
            "source_predicate": raw.get("predicate"),
        },
    }


def transform_file(input_path: Path, output_path: Path) -> None:
    raw = json.loads(input_path.read_text(encoding="utf-8"))
    transformed = transform_semantic_explanation(raw, input_path.name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(transformed, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transform Jason semantic_explanation raw JSON into cleaner semantic JSON."
    )
    parser.add_argument(
        "--input-dir",
        default="mas/outputs/semantic_explanations",
        help="Directory containing the raw Jason-exported JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/transformed",
        help="Directory where the cleaned semantic JSON files will be written.",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.exists():
        raise SystemExit(f"Input directory does not exist: {input_dir}")

    transformed_files = []
    for input_path in sorted(input_dir.glob("*.json")):
        output_path = output_dir / input_path.name
        transform_file(input_path, output_path)
        transformed_files.append(output_path)

    index_path = output_dir / "index.json"
    index_payload = {
        "count": len(transformed_files),
        "files": [path.name for path in transformed_files],
    }
    index_path.write_text(
        json.dumps(index_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Transformed {len(transformed_files)} files into {output_dir}")


if __name__ == "__main__":
    main()
