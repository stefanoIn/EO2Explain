#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from owlready2 import get_ontology

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def generated_individuals(onto, suffix: str):
    return sorted(
        [individual for individual in onto.individuals() if individual.name.endswith(suffix)],
        key=lambda individual: individual.name,
    )


def prop_values(individual, property_name: str) -> list:
    return list(getattr(individual, property_name, []))


def single_value(individual, property_name: str):
    values = prop_values(individual, property_name)
    return values[0] if values else None


def assessment_record(event) -> dict[str, str]:
    assessment = prop_values(event, "hasAssessment")[0]
    clarification = prop_values(assessment, "hasClarification")[0]
    bundle = prop_values(assessment, "hasEvidenceBundle")[0]
    event_name = single_value(event, "hasName") or event.name
    hazard = prop_values(assessment, "hasHazard")[0].name.replace("_hazard", "")
    severity = prop_values(assessment, "hasSeverity")[0].name.replace("_severity", "")
    confidence = prop_values(assessment, "hasConfidence")[0].name.replace("_confidence", "")
    support = single_value(assessment, "hasSupportLevel") or "unknown"
    conclusion_status = single_value(assessment, "hasConclusionStatus") or "unknown"
    clarification_status = single_value(clarification, "hasClarificationStatus") or "unknown"
    primary_caveat = single_value(bundle, "hasPrimaryCaveatLabel") or "none"
    return {
        "event_id": event.name.removesuffix("_event"),
        "event_name": event_name,
        "hazard": hazard,
        "severity": severity,
        "confidence": confidence,
        "support_level": support,
        "conclusion_status": conclusion_status,
        "clarification_status": clarification_status,
        "primary_caveat": primary_caveat,
    }


def build_query_summary(ontology_path: Path) -> dict:
    onto = get_ontology(str(ontology_path)).load()
    records = [assessment_record(event) for event in generated_individuals(onto, "_event")]

    return {
        "counts": {
            "events": len(records),
            "severe_floods": sum(1 for item in records if item["hazard"] == "flood" and item["severity"] == "severe"),
            "low_confidence_cases": sum(1 for item in records if item["confidence"] == "low"),
            "inconclusive_cases": sum(1 for item in records if item["conclusion_status"] == "inconclusive"),
            "late_observation_cases": sum(1 for item in records if item["primary_caveat"] == "late_observation"),
            "clarification_cases": sum(1 for item in records if item["clarification_status"] == "clarification_provided"),
            "weak_support_medium_confidence_cases": sum(
                1 for item in records if item["support_level"] == "weak" and item["confidence"] == "medium"
            ),
            "weak_or_conflicting_support_cases": sum(
                1 for item in records if item["support_level"] in {"weak", "conflicting", "insufficient"}
            ),
        },
        "queries": {
            "severe_floods": [item for item in records if item["hazard"] == "flood" and item["severity"] == "severe"],
            "low_confidence_cases": [item for item in records if item["confidence"] == "low"],
            "inconclusive_cases": [item for item in records if item["conclusion_status"] == "inconclusive"],
            "late_observation_cases": [item for item in records if item["primary_caveat"] == "late_observation"],
            "clarification_cases": [item for item in records if item["clarification_status"] == "clarification_provided"],
            "weak_support_medium_confidence_cases": [
                item for item in records if item["support_level"] == "weak" and item["confidence"] == "medium"
            ],
            "clarification_cases_by_hazard": {
                hazard: [item for item in records if item["hazard"] == hazard and item["clarification_status"] == "clarification_provided"]
                for hazard in sorted({item["hazard"] for item in records})
            },
            "weak_or_conflicting_support_cases": [
                item for item in records if item["support_level"] in {"weak", "conflicting", "insufficient"}
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate simple query summaries from the populated EO2Explain ontology."
    )
    parser.add_argument(
        "--ontology",
        default="nlp/ontology/eo2explain_populated.rdf",
        help="Populated ontology RDF/XML file.",
    )
    parser.add_argument(
        "--output",
        default="outputs/ontology_query_summary.json",
        help="Output path for the ontology query summary JSON.",
    )
    args = parser.parse_args()

    ontology_path = Path(args.ontology)
    if not ontology_path.is_absolute():
        ontology_path = PROJECT_ROOT / ontology_path

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    if not ontology_path.exists():
        raise SystemExit(f"Ontology file does not exist: {ontology_path}")

    summary = build_query_summary(ontology_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Ontology query summary written to {output_path}")


if __name__ == "__main__":
    main()
