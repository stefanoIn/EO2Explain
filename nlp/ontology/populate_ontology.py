#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


BASE_IRI = "http://www.semanticweb.org/stefanoinfusini/ontologies/2026/3/eo2explain"
NS = {
    "eo2explain": f"{BASE_IRI}#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}

ET.register_namespace("eo2explain", NS["eo2explain"])
ET.register_namespace("owl", NS["owl"])
ET.register_namespace("rdf", NS["rdf"])
ET.register_namespace("rdfs", NS["rdfs"])


def iri(local_name: str) -> str:
    return f"{BASE_IRI}#{local_name}"


def load_payloads(payload_dir: Path) -> list[dict]:
    payloads = []
    for path in sorted(payload_dir.glob("*.json")):
        if path.name == "index.json":
            continue
        payloads.append(json.loads(path.read_text(encoding="utf-8")))
    return payloads


def named_individuals(root: ET.Element) -> list[ET.Element]:
    return root.findall(f"{{{NS['owl']}}}NamedIndividual")


def find_named_individual(root: ET.Element, local_name: str) -> ET.Element | None:
    target = iri(local_name)
    for element in named_individuals(root):
        if element.get(f"{{{NS['rdf']}}}about") == target:
            return element
    return None


def remove_named_individual(root: ET.Element, local_name: str) -> None:
    element = find_named_individual(root, local_name)
    if element is not None:
        root.remove(element)


def remove_generated_nodes(root: ET.Element, event_id: str) -> None:
    suffixes = [
        "event",
        "assessment",
        "evidence_bundle",
        "clarification",
        "provenance",
        "explanation_trace",
    ]
    for suffix in suffixes:
        remove_named_individual(root, f"{event_id}_{suffix}")


def create_named_individual(root: ET.Element, local_name: str, class_local: str) -> ET.Element:
    individual = ET.SubElement(
        root,
        f"{{{NS['owl']}}}NamedIndividual",
        {f"{{{NS['rdf']}}}about": iri(local_name)},
    )
    ET.SubElement(
        individual,
        f"{{{NS['rdf']}}}type",
        {f"{{{NS['rdf']}}}resource": iri(class_local)},
    )
    return individual


def ensure_individual(
    root: ET.Element,
    local_name: str,
    class_local: str,
    *,
    label: str | None = None,
) -> ET.Element:
    individual = find_named_individual(root, local_name)
    if individual is None:
        individual = create_named_individual(root, local_name, class_local)
    if label:
        set_text_property(individual, "hasName", label)
    return individual


def set_text_property(individual: ET.Element, property_name: str, value: str) -> None:
    tag = f"{{{NS['eo2explain']}}}{property_name}"
    for child in list(individual.findall(tag)):
        individual.remove(child)
    prop = ET.SubElement(individual, tag)
    prop.text = value


def add_object_property(individual: ET.Element, property_name: str, target_local: str) -> None:
    tag = f"{{{NS['eo2explain']}}}{property_name}"
    ET.SubElement(individual, tag, {f"{{{NS['rdf']}}}resource": iri(target_local)})


def meaningful_name(value: str | None) -> bool:
    return value is not None and value not in {
        "none",
        "no_major_caveat",
        "no_alternative_claim",
        "no_additional_limitation",
    }


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


def populate_controlled_terms(root: ET.Element, payload: dict) -> None:
    event = payload["event"]
    assessment = payload["assessment"]
    evidence = payload["evidence"]
    clarification = payload["clarification"]
    provenance = payload["provenance"]

    hazard_local, hazard_class = hazard_individual(event["hazard_type"])
    ensure_individual(root, hazard_local, hazard_class, label=event["hazard_type"].capitalize())
    ensure_individual(root, severity_individual(assessment["severity"]), "Severity")
    ensure_individual(root, confidence_individual(assessment["fusion_confidence"]), "ConfidenceLevel")
    ensure_individual(root, exposure_individual(assessment["exposure_class"]), "ExposureLevel")
    ensure_individual(root, concern_individual(assessment["concern_level"]), "ConcernLevel")
    ensure_individual(root, claim_individual(assessment["claim_label"]), "ClaimLabel", label=assessment["claim_label"])
    ensure_individual(root, agent_individual(provenance["source_agent"]), "Agent", label=provenance["source_agent"])
    ensure_individual(root, rule_individual(provenance["rule_label"]), "Rule", label=provenance["rule_label"])
    ensure_individual(root, event["country"]["id"], "Country", label=event["country"]["name"])
    ensure_individual(root, event["region"]["id"], "Region", label=event["region"]["name"])

    if meaningful_name(clarification.get("alternative_claim")):
        ensure_individual(
            root,
            claim_individual(clarification["alternative_claim"]),
            "ClaimLabel",
            label=clarification["alternative_claim"],
        )

    evidence_names = set(evidence["evidence_items"])
    if meaningful_name(evidence.get("strongest_evidence")):
        evidence_names.add(evidence["strongest_evidence"])
    for evidence_name in evidence_names:
        ensure_individual(root, evidence_name, "Evidence")

    caveat_names = set(evidence["caveat_items"])
    if meaningful_name(evidence.get("primary_caveat")):
        caveat_names.add(evidence["primary_caveat"])
    if meaningful_name(clarification.get("primary_limitation")):
        caveat_names.add(clarification["primary_limitation"])
    for caveat_name in caveat_names:
        ensure_individual(root, caveat_name, "Caveat")


def populate_event(root: ET.Element, payload: dict) -> None:
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

    remove_generated_nodes(root, event_id)
    populate_controlled_terms(root, payload)

    hazard_local, hazard_class = hazard_individual(event["hazard_type"])
    ensure_individual(root, hazard_local, hazard_class, label=event["hazard_type"].capitalize())

    event_individual = create_named_individual(root, event_local, "Event")
    set_text_property(event_individual, "hasEventId", event_id)
    set_text_property(event_individual, "hasName", event["event_name"])
    add_object_property(event_individual, "hasCountry", event["country"]["id"])
    add_object_property(event_individual, "hasRegion", event["region"]["id"])
    add_object_property(event_individual, "hasAssessment", assessment_local)
    add_object_property(event_individual, "hasExplanationTrace", trace_local)

    assessment_individual = create_named_individual(root, assessment_local, "Assessment")
    set_text_property(assessment_individual, "hasClaimLabel", assessment["claim_label"])
    set_text_property(assessment_individual, "hasCaseProfile", assessment["case_profile"])
    set_text_property(assessment_individual, "hasInterpretationMode", assessment["interpretation_mode"])
    add_object_property(assessment_individual, "hasHazard", hazard_local)
    add_object_property(assessment_individual, "hasClaim", claim_individual(assessment["claim_label"]))
    add_object_property(assessment_individual, "hasSeverity", severity_individual(assessment["severity"]))
    add_object_property(assessment_individual, "hasConfidence", confidence_individual(assessment["fusion_confidence"]))
    add_object_property(assessment_individual, "hasExposure", exposure_individual(assessment["exposure_class"]))
    add_object_property(assessment_individual, "hasConcern", concern_individual(assessment["concern_level"]))
    add_object_property(assessment_individual, "hasEvidenceBundle", bundle_local)
    add_object_property(assessment_individual, "hasClarification", clarification_local)
    add_object_property(assessment_individual, "hasProvenance", provenance_local)

    bundle_individual = create_named_individual(root, bundle_local, "EvidenceBundle")
    for evidence_name in evidence["evidence_items"]:
        add_object_property(bundle_individual, "hasEvidenceItem", evidence_name)
    if meaningful_name(evidence.get("strongest_evidence")):
        add_object_property(bundle_individual, "hasStrongestEvidence", evidence["strongest_evidence"])
    for caveat_name in evidence["caveat_items"]:
        add_object_property(bundle_individual, "hasCaveat", caveat_name)
    if meaningful_name(evidence.get("primary_caveat")):
        add_object_property(bundle_individual, "hasPrimaryCaveat", evidence["primary_caveat"])

    clarification_individual = create_named_individual(root, clarification_local, "Clarification")
    set_text_property(clarification_individual, "hasClarificationStatus", clarification["clarification_status"])
    set_text_property(clarification_individual, "hasAlternativeClaimLabel", clarification["alternative_claim"])
    if meaningful_name(clarification.get("primary_limitation")):
        add_object_property(clarification_individual, "hasPrimaryLimitation", clarification["primary_limitation"])
    if meaningful_name(clarification.get("alternative_claim")):
        add_object_property(
            clarification_individual,
            "hasAlternativeClaim",
            claim_individual(clarification["alternative_claim"]),
        )

    provenance_individual = create_named_individual(root, provenance_local, "Provenance")
    set_text_property(provenance_individual, "hasSourceAgent", provenance["source_agent"])
    set_text_property(provenance_individual, "hasRuleLabel", provenance["rule_label"])
    add_object_property(provenance_individual, "hasSourceAgentEntity", agent_individual(provenance["source_agent"]))
    add_object_property(provenance_individual, "hasRule", rule_individual(provenance["rule_label"]))

    trace_individual = create_named_individual(root, trace_local, "ExplanationTrace")
    set_text_property(trace_individual, "hasHeadline", debug["short_headline"])
    set_text_property(trace_individual, "hasSummary", debug["short_summary"])
    add_object_property(trace_individual, "tracesAssessment", assessment_local)
    add_object_property(trace_individual, "tracesEvidenceBundle", bundle_local)
    add_object_property(trace_individual, "tracesClarification", clarification_local)
    add_object_property(trace_individual, "tracesProvenance", provenance_local)


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

    tree = ET.parse(Path(args.ontology))
    root = tree.getroot()

    for payload in load_payloads(Path(args.payload_dir)):
        populate_event(root, payload)

    ET.indent(tree, space="    ")
    tree.write(Path(args.output), encoding="utf-8", xml_declaration=True)
    print(f"Populated ontology written to {args.output}")


if __name__ == "__main__":
    main()
