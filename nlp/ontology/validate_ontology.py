#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

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


def validate_ontology(ontology_path: Path) -> list[str]:
    onto = get_ontology(str(ontology_path)).load()
    errors: list[str] = []

    events = generated_individuals(onto, "_event")
    assessments = generated_individuals(onto, "_assessment")

    assessment_to_event: dict[str, object] = {}

    for event in events:
        linked_assessments = prop_values(event, "hasAssessment")
        if len(linked_assessments) != 1:
            errors.append(
                f"{event.name}: expected exactly one assessment, found {len(linked_assessments)}"
            )
            continue
        assessment_to_event[linked_assessments[0].name] = event

    for assessment in assessments:
        severities = prop_values(assessment, "hasSeverity")
        confidences = prop_values(assessment, "hasConfidence")
        support_levels = prop_values(assessment, "hasSupportLevel")
        conclusion_statuses = prop_values(assessment, "hasConclusionStatus")
        support_categories = prop_values(assessment, "hasSupportCategory")
        conclusion_status_entities = prop_values(assessment, "hasConclusionStatusEntity")
        clarifications = prop_values(assessment, "hasClarification")
        bundles = prop_values(assessment, "hasEvidenceBundle")

        if len(severities) != 1:
            errors.append(
                f"{assessment.name}: expected exactly one severity, found {len(severities)}"
            )
        if len(confidences) != 1:
            errors.append(
                f"{assessment.name}: expected exactly one confidence, found {len(confidences)}"
            )
        if len(support_levels) != 1:
            errors.append(
                f"{assessment.name}: expected exactly one support level, found {len(support_levels)}"
            )
        if len(conclusion_statuses) != 1:
            errors.append(
                f"{assessment.name}: expected exactly one conclusion status, found {len(conclusion_statuses)}"
            )
        if len(support_categories) != 1:
            errors.append(
                f"{assessment.name}: expected exactly one support category entity, found {len(support_categories)}"
            )
        if len(conclusion_status_entities) != 1:
            errors.append(
                f"{assessment.name}: expected exactly one conclusion status entity, found {len(conclusion_status_entities)}"
            )
        if len(clarifications) != 1:
            errors.append(
                f"{assessment.name}: expected exactly one clarification node, found {len(clarifications)}"
            )
        if len(bundles) != 1:
            errors.append(
                f"{assessment.name}: expected exactly one evidence bundle, found {len(bundles)}"
            )

        conclusion_status = conclusion_statuses[0] if conclusion_statuses else None
        confidence_individual = confidences[0] if confidences else None
        confidence_name = getattr(confidence_individual, "name", "")
        severity_individual = severities[0] if severities else None
        severity_name = getattr(severity_individual, "name", "")
        support_level = support_levels[0] if support_levels else None
        claim_label = single_value(assessment, "hasClaimLabel")
        if conclusion_status == "inconclusive" and confidence_name == "high_confidence":
            errors.append(
                f"{assessment.name}: inconclusive assessments must not be linked to high confidence"
            )
        if support_level == "insufficient" and severity_name != "undetermined_severity":
            errors.append(
                f"{assessment.name}: insufficient support should map to undetermined severity"
            )
        if conclusion_status == "inconclusive" and claim_label not in {
            "inconclusive_fire_signal",
            "inconclusive_water_signal",
        }:
            errors.append(
                f"{assessment.name}: inconclusive assessments must use an inconclusive claim label"
            )

        if clarifications:
            clarification = clarifications[0]
            clarification_status = single_value(clarification, "hasClarificationStatus")
            if clarification_status == "clarification_provided":
                primary_limitation_label = single_value(clarification, "hasPrimaryLimitationLabel")
                if primary_limitation_label in (None, "", "none"):
                    errors.append(
                        f"{assessment.name}: clarification_provided requires a primary limitation"
                    )

                if bundles:
                    strongest_evidence_label = single_value(
                        bundles[0], "hasStrongestEvidenceLabel"
                    )
                    if strongest_evidence_label in (None, "", "none"):
                        errors.append(
                            f"{assessment.name}: clarification_provided requires strongest evidence"
                        )
            if clarification_status == "no_clarification":
                primary_limitation_label = single_value(
                    clarification, "hasPrimaryLimitationLabel"
                )
                if primary_limitation_label not in {
                    "no_additional_limitation",
                    None,
                    "",
                }:
                    errors.append(
                        f"{assessment.name}: no_clarification should not keep a non-empty limitation label"
                    )

        if bundles:
            bundle = bundles[0]
            primary_caveat = single_value(bundle, "hasPrimaryCaveatLabel")
            caveat_labels_raw = single_value(bundle, "hasCaveatLabel") or ""
            caveat_labels = [
                label for label in caveat_labels_raw.split("|") if label and label != "no_major_caveat"
            ]
            if primary_caveat == "no_major_caveat" and any(
                label not in {"no_major_caveat", "neutral_observation_context"}
                for label in caveat_labels
            ):
                errors.append(
                    f"{assessment.name}: no_major_caveat should not coexist with substantive caveat labels"
                )

        if assessment.name not in assessment_to_event:
            errors.append(
                f"{assessment.name}: assessment is not linked from exactly one generated event"
            )

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate populated EO2Explain ontology outputs."
    )
    parser.add_argument(
        "--ontology",
        default="nlp/ontology/eo2explain_populated.rdf",
        help="Populated ontology RDF/XML file.",
    )
    args = parser.parse_args()

    ontology_path = Path(args.ontology)
    if not ontology_path.is_absolute():
        ontology_path = PROJECT_ROOT / ontology_path

    if not ontology_path.exists():
        raise SystemExit(f"Ontology file does not exist: {ontology_path}")

    errors = validate_ontology(ontology_path)
    if errors:
        print("Ontology validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("Ontology validation passed.")


if __name__ == "__main__":
    main()
