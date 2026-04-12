#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import types

from owlready2 import DataProperty, destroy_entity, get_ontology

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BASE_IRI = "http://www.semanticweb.org/stefanoinfusini/ontologies/2026/3/eo2explain"


def load_payloads(payload_dir: Path) -> list[dict]:
    payloads = []
    for path in sorted(payload_dir.glob("*.json")):
        if path.name == "index.json":
            continue
        payloads.append(json.loads(path.read_text(encoding="utf-8")))
    return payloads


def meaningful_name(value: str | None) -> bool:
    return value is not None and value not in {
        "none",
        "no_major_caveat",
        "no_alternative_claim",
        "no_additional_limitation",
    }


def get_entity(onto, local_name: str):
    return onto.search_one(iri=f"{BASE_IRI}#{local_name}")


def get_class(ns, class_name: str):
    cls = getattr(ns, class_name, None)
    if cls is None:
        raise ValueError(f"Missing ontology class: {class_name}")
    return cls


def ensure_data_property(ns, property_name: str):
    prop = getattr(ns, property_name, None)
    if prop is None:
        with ns.ontology:
            prop = types.new_class(property_name, (DataProperty,))
    return prop


def ensure_individual(onto, ns, local_name: str, class_name: str):
    entity = get_entity(onto, local_name)
    if entity is None:
        entity = get_class(ns, class_name)(local_name)
    return entity


def ensure_generated_individual(onto, ns, local_name: str, class_name: str):
    """Create or recover event-scoped generated individuals."""
    return ensure_individual(onto, ns, local_name, class_name)


def set_single_data_property(individual, property_name: str, value: str) -> None:
    """Treat the target data property as single-valued for this project."""
    prop = ensure_data_property(individual.namespace, property_name)
    prop[individual] = [value]


def set_object_properties(individual, property_name: str, targets: list) -> None:
    relation = getattr(individual, property_name)
    relation.clear()
    for target in targets:
        relation.append(target)


def hazard_individual(hazard: str) -> tuple[str, str]:
    mapping = {
        "flood": ("flood_hazard", "Flood"),
        "wildfire": ("wildfire_hazard", "Wildfire"),
    }
    return mapping[hazard]


def severity_individual(severity: str) -> str:
    return f"{severity}_severity"


def confidence_individual(confidence: str) -> str:
    return f"{confidence}_confidence"


def exposure_individual(exposure: str) -> str:
    return f"{exposure}_exposure"


def concern_individual(concern: str) -> str:
    return f"{concern}_concern"


def claim_individual(claim: str) -> str:
    return f"{claim}_claim"


def rule_individual(rule: str) -> str:
    return f"{rule}_rule"


def agent_individual(agent: str) -> str:
    return f"{agent}_entity"


def remove_generated_nodes(onto, event_id: str) -> None:
    # Only destroy event-scoped generated nodes. Shared vocabulary terms such as
    # hazards, caveats, rules, agents, and claim labels must remain untouched.
    for suffix in [
        "event",
        "assessment",
        "evidence_bundle",
        "clarification",
        "provenance",
        "explanation_trace",
    ]:
        entity = get_entity(onto, f"{event_id}_{suffix}")
        if entity is not None:
            destroy_entity(entity)


def populate_controlled_terms(onto, ns, payload: dict) -> None:
    event = payload["event"]
    assessment = payload["assessment"]
    evidence = payload["evidence"]
    clarification = payload["clarification"]
    provenance = payload["provenance"]

    hazard_local, hazard_class = hazard_individual(event["hazard_type"])
    hazard = ensure_individual(onto, ns, hazard_local, hazard_class)
    set_single_data_property(hazard, "hasName", event["hazard_type"].capitalize())

    ensure_individual(onto, ns, severity_individual(assessment["severity"]), "Severity")
    ensure_individual(onto, ns, confidence_individual(assessment["fusion_confidence"]), "ConfidenceLevel")
    ensure_individual(onto, ns, exposure_individual(assessment["exposure_class"]), "ExposureLevel")
    ensure_individual(onto, ns, concern_individual(assessment["concern_level"]), "ConcernLevel")

    claim = ensure_individual(onto, ns, claim_individual(assessment["claim_label"]), "ClaimLabel")
    set_single_data_property(claim, "hasName", assessment["claim_label"])

    agent = ensure_individual(onto, ns, agent_individual(provenance["source_agent"]), "Agent")
    set_single_data_property(agent, "hasName", provenance["source_agent"])

    rule = ensure_individual(onto, ns, rule_individual(provenance["rule_label"]), "Rule")
    set_single_data_property(rule, "hasName", provenance["rule_label"])

    country = ensure_individual(onto, ns, event["country"]["id"], "Country")
    set_single_data_property(country, "hasName", event["country"]["name"])

    region = ensure_individual(onto, ns, event["region"]["id"], "Region")
    set_single_data_property(region, "hasName", event["region"]["name"])

    if meaningful_name(clarification.get("alternative_claim")):
        alt_claim = ensure_individual(
            onto,
            ns,
            claim_individual(clarification["alternative_claim"]),
            "ClaimLabel",
        )
        set_single_data_property(alt_claim, "hasName", clarification["alternative_claim"])

    evidence_names = set(evidence["evidence_items"])
    if meaningful_name(evidence.get("strongest_evidence")):
        evidence_names.add(evidence["strongest_evidence"])
    for evidence_name in evidence_names:
        ensure_individual(onto, ns, evidence_name, "Evidence")

    caveat_names = set(evidence["caveat_items"])
    if meaningful_name(evidence.get("primary_caveat")):
        caveat_names.add(evidence["primary_caveat"])
    if meaningful_name(clarification.get("primary_limitation")):
        caveat_names.add(clarification["primary_limitation"])
    for caveat_name in caveat_names:
        ensure_individual(onto, ns, caveat_name, "Caveat")


def populate_event(onto, ns, payload: dict) -> None:
    event = payload["event"]
    assessment = payload["assessment"]
    evidence = payload["evidence"]
    clarification = payload["clarification"]
    provenance = payload["provenance"]
    debug = payload["debug"]

    event_id = payload["event_id"]
    event_local = f"{event_id}_event"
    assessment_local = f"{event_id}_assessment"
    bundle_local = f"{event_id}_evidence_bundle"
    clarification_local = f"{event_id}_clarification"
    provenance_local = f"{event_id}_provenance"
    trace_local = f"{event_id}_explanation_trace"

    remove_generated_nodes(onto, event_id)
    populate_controlled_terms(onto, ns, payload)

    hazard_local, _ = hazard_individual(event["hazard_type"])

    event_individual = ensure_generated_individual(onto, ns, event_local, "Event")
    set_single_data_property(event_individual, "hasEventId", event_id)
    set_single_data_property(event_individual, "hasName", event["event_name"])
    set_object_properties(
        event_individual,
        "hasCountry",
        [get_entity(onto, event["country"]["id"])],
    )
    set_object_properties(
        event_individual,
        "hasRegion",
        [get_entity(onto, event["region"]["id"])],
    )
    set_object_properties(
        event_individual,
        "hasAssessment",
        [ensure_generated_individual(onto, ns, assessment_local, "Assessment")],
    )
    set_object_properties(
        event_individual,
        "hasExplanationTrace",
        [ensure_generated_individual(onto, ns, trace_local, "ExplanationTrace")],
    )

    assessment_individual = ensure_generated_individual(onto, ns, assessment_local, "Assessment")
    # The ontology keeps both string labels and semantic links:
    # - string properties support direct reporting/debug access
    # - object properties support ontology querying
    set_single_data_property(assessment_individual, "hasClaimLabel", assessment["claim_label"])
    set_single_data_property(assessment_individual, "hasCaseProfile", assessment["case_profile"])
    set_single_data_property(assessment_individual, "hasInterpretationMode", assessment["interpretation_mode"])
    set_single_data_property(
        assessment_individual,
        "hasSupportLevel",
        assessment.get("support_level", "not_available"),
    )
    set_single_data_property(
        assessment_individual,
        "hasConclusionStatus",
        assessment.get("conclusion_status", "hazard_assessed"),
    )
    set_object_properties(assessment_individual, "hasHazard", [get_entity(onto, hazard_local)])
    set_object_properties(
        assessment_individual,
        "hasClaim",
        [get_entity(onto, claim_individual(assessment["claim_label"]))],
    )
    set_object_properties(
        assessment_individual,
        "hasSeverity",
        [get_entity(onto, severity_individual(assessment["severity"]))],
    )
    set_object_properties(
        assessment_individual,
        "hasConfidence",
        [get_entity(onto, confidence_individual(assessment["fusion_confidence"]))],
    )
    set_object_properties(
        assessment_individual,
        "hasExposure",
        [get_entity(onto, exposure_individual(assessment["exposure_class"]))],
    )
    set_object_properties(
        assessment_individual,
        "hasConcern",
        [get_entity(onto, concern_individual(assessment["concern_level"]))],
    )
    set_object_properties(
        assessment_individual,
        "hasEvidenceBundle",
        [ensure_generated_individual(onto, ns, bundle_local, "EvidenceBundle")],
    )
    set_object_properties(
        assessment_individual,
        "hasClarification",
        [ensure_generated_individual(onto, ns, clarification_local, "Clarification")],
    )
    set_object_properties(
        assessment_individual,
        "hasProvenance",
        [ensure_generated_individual(onto, ns, provenance_local, "Provenance")],
    )

    bundle_individual = ensure_generated_individual(onto, ns, bundle_local, "EvidenceBundle")
    set_object_properties(
        bundle_individual,
        "hasEvidenceItem",
        [get_entity(onto, evidence_name) for evidence_name in evidence["evidence_items"]],
    )
    strongest_targets = []
    if meaningful_name(evidence.get("strongest_evidence")):
        strongest_targets.append(get_entity(onto, evidence["strongest_evidence"]))
    set_object_properties(bundle_individual, "hasStrongestEvidence", strongest_targets)
    set_object_properties(
        bundle_individual,
        "hasCaveat",
        [get_entity(onto, caveat_name) for caveat_name in evidence["caveat_items"]],
    )
    primary_caveat_targets = []
    if meaningful_name(evidence.get("primary_caveat")):
        primary_caveat_targets.append(get_entity(onto, evidence["primary_caveat"]))
    set_object_properties(bundle_individual, "hasPrimaryCaveat", primary_caveat_targets)

    clarification_individual = ensure_generated_individual(onto, ns, clarification_local, "Clarification")
    set_single_data_property(
        clarification_individual,
        "hasClarificationStatus",
        clarification["clarification_status"],
    )
    set_single_data_property(
        clarification_individual,
        "hasAlternativeClaimLabel",
        clarification["alternative_claim"],
    )
    primary_limitation_targets = []
    if meaningful_name(clarification.get("primary_limitation")):
        primary_limitation_targets.append(get_entity(onto, clarification["primary_limitation"]))
    set_object_properties(
        clarification_individual,
        "hasPrimaryLimitation",
        primary_limitation_targets,
    )
    alternative_claim_targets = []
    if meaningful_name(clarification.get("alternative_claim")):
        alternative_claim_targets.append(
            get_entity(onto, claim_individual(clarification["alternative_claim"]))
        )
    set_object_properties(
        clarification_individual,
        "hasAlternativeClaim",
        alternative_claim_targets,
    )

    provenance_individual = ensure_generated_individual(onto, ns, provenance_local, "Provenance")
    set_single_data_property(provenance_individual, "hasSourceAgent", provenance["source_agent"])
    set_single_data_property(provenance_individual, "hasRuleLabel", provenance["rule_label"])
    set_object_properties(
        provenance_individual,
        "hasSourceAgentEntity",
        [get_entity(onto, agent_individual(provenance["source_agent"]))],
    )
    set_object_properties(
        provenance_individual,
        "hasRule",
        [get_entity(onto, rule_individual(provenance["rule_label"]))],
    )

    trace_individual = ensure_generated_individual(onto, ns, trace_local, "ExplanationTrace")
    set_single_data_property(trace_individual, "hasHeadline", debug["short_headline"])
    set_single_data_property(trace_individual, "hasSummary", debug["short_summary"])
    set_object_properties(trace_individual, "tracesAssessment", [assessment_individual])
    set_object_properties(trace_individual, "tracesEvidenceBundle", [bundle_individual])
    set_object_properties(trace_individual, "tracesClarification", [clarification_individual])
    set_object_properties(trace_individual, "tracesProvenance", [provenance_individual])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Populate the EO2Explain ontology from transformed semantic JSON payloads."
    )
    parser.add_argument(
        "--ontology",
        default="nlp/ontology/eo2explain.rdf",
        help="Source ontology RDF/XML file exported from Protege.",
    )
    parser.add_argument(
        "--payload-dir",
        default="outputs/transformed",
        help="Directory containing transformed semantic payload JSON files.",
    )
    parser.add_argument(
        "--output",
        default="nlp/ontology/eo2explain_populated.rdf",
        help="Output path for the populated RDF/XML ontology.",
    )
    args = parser.parse_args()

    ontology_path = Path(args.ontology)
    if not ontology_path.is_absolute():
        ontology_path = PROJECT_ROOT / ontology_path

    payload_dir = Path(args.payload_dir)
    if not payload_dir.is_absolute():
        payload_dir = PROJECT_ROOT / payload_dir

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = PROJECT_ROOT / output_path

    onto = get_ontology(str(ontology_path)).load()
    ns = onto.get_namespace(f"{BASE_IRI}#")

    for payload in load_payloads(payload_dir):
        populate_event(onto, ns, payload)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    onto.save(file=str(output_path), format="rdfxml")
    print(f"Populated ontology written to {output_path}")


if __name__ == "__main__":
    main()
