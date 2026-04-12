#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nlp.loader.load_payloads import load_payloads


EVIDENCE_LABELS = {
    "water_increase_pct": "surface-water increase",
    "water_area_before_pct": "pre-event water coverage",
    "newly_flooded_area_pct": "newly flooded area",
    "ndwi_change": "NDWI change",
    "vegetation_loss_pct": "vegetation loss",
    "burned_area_pct": "burned-area extent",
    "mean_dnbr": "mean dNBR burn severity",
    "ndvi_drop": "NDVI drop",
    "no_dominant_evidence": "no single strongest evidence item",
}

ALTERNATIVE_CLAIM_TEXT = {
    "inconclusive_fire_signal": "an inconclusive fire signal",
    "inconclusive_water_signal": "an inconclusive water signal",
    "no_alternative_claim": "no alternative claim",
}

CAVEAT_TEXT = {
    "coastal_baseline_water": "the scene already contains substantial pre-event coastal or permanent water, which can mimic flood-like spectral change",
    "late_observation": "post-event imagery was acquired late, so peak impact may no longer be fully visible",
    "no_flood_expansion": "no meaningful flooded-area expansion was detected beyond the pre-event water baseline",
    "possible_underestimation": "the measured footprint may underestimate the real extent of the event",
    "weak_water_signal": "the water signal is weak and must be interpreted cautiously",
    "burn_signal_weak": "the burn signal is weak or partly contradictory",
    "timeline_uncertain": "the event timeline mixes confirmed and approximate temporal information",
    "coarse_timeline": "the event timing is only coarsely constrained",
    "residual_observation_window": "the observed footprint likely reflects residual conditions rather than peak impact",
    "limited_multisignal_support": "the interpretation is not supported by a full set of corroborating signals",
}

CAVEAT_LIST_TEXT = {
    "coastal_baseline_water": "substantial pre-event coastal or permanent water in the scene",
    "late_observation": "late image acquisition",
    "no_flood_expansion": "no meaningful flooded-area expansion beyond the pre-event baseline",
    "possible_underestimation": "possible underestimation of the event extent",
    "weak_water_signal": "a weak water signal that must be interpreted cautiously",
    "burn_signal_weak": "a weak or partly contradictory burn signal",
    "timeline_uncertain": "a timeline mixing confirmed and approximate temporal information",
    "coarse_timeline": "coarse temporal constraints on the event timing",
    "residual_observation_window": "an observed footprint that likely reflects residual conditions rather than peak impact",
    "limited_multisignal_support": "limited multisignal support",
}

CONCERN_TEXT = {
    "critical": "This means the event should be treated as a critical case requiring immediate attention.",
    "high": "This means the event should be treated as a high-priority case.",
    "elevated": "This means the event should be treated as an elevated concern that deserves careful monitoring.",
    "moderate": "This means the event should be monitored as a moderate concern.",
    "guarded": "This means the event should be handled cautiously because the situation remains uncertain or limited in scope.",
    "watch": "This means the event is currently in watch status and should be monitored for possible escalation.",
}

CASE_PROFILE_TEXT = {
    "critical_concern_case": "This indicates a critical situation requiring immediate attention.",
    "high_priority_event": "This indicates a high-priority situation that should remain under close observation.",
    "confidence_limited_priority_event": "This indicates a high-priority situation, but with confidence limitations that require a cautious reading.",
    "elevated_priority_event": "This indicates an elevated-priority situation that deserves close monitoring.",
    "cautious_monitoring_case": "This indicates a monitoring case that should be interpreted cautiously because of remaining uncertainty.",
    "monitoring_case": "This indicates a situation that should remain under routine monitoring.",
    "guarded_monitoring_case": "This indicates a situation that should be monitored cautiously due to remaining uncertainty.",
    "watch_case": "This indicates a watch-level situation that should be monitored for possible escalation.",
}

CLAIM_TEXT = {
    "strong_multisignal_fire_damage": "The wildfire assessment is supported by a strong multi-signal pattern combining vegetation loss, burned-area extent, and spectral burn severity.",
    "strong_multisignal_flooding": "The flood assessment is supported by a strong multi-signal pattern combining water expansion, newly flooded area, and spectral water change.",
    "coherent_flooding": "The flood assessment is supported by mutually consistent evidence across water expansion, newly flooded area, and spectral water change.",
    "extent_supported_flooding": "The flood assessment is supported mainly by water expansion and newly flooded area, although the spectral water signal is less decisive.",
    "residual_flood_signal": "The system detects a residual flood footprint, suggesting that flood impact remains visible even though the image may have missed peak conditions.",
    "limited_water_shift_signal": "The flood assessment is driven mainly by a limited spectral water shift rather than by a strong spatial flood footprint.",
    "mixed_flood_signal": "The flood indicators point to a possible flood footprint, but the spectral water signal conflicts with the spatial extent evidence.",
    "inconclusive_water_signal": "The available water-related evidence remains inconclusive.",
    "coherent_fire_damage": "The wildfire assessment is supported by consistent vegetation-loss and burned-area evidence.",
    "spectral_extent_fire_damage": "The wildfire assessment is supported by burn extent together with spectral burn-severity evidence.",
    "mixed_fire_damage": "Wildfire damage is still indicated, but the spectral burn evidence is mixed relative to the vegetation-loss and burned-area signals.",
    "ndvi_only_fire_signal": "The wildfire assessment is driven mainly by vegetation change, with limited support from burn extent or spectral burn evidence.",
    "vegetation_loss_only_fire_signal": "The wildfire assessment is supported mainly by vegetation-loss evidence.",
    "inconclusive_fire_signal": "The available fire-related evidence remains inconclusive.",
}

CONFIDENCE_TEXT = {
    "high": "The system treats this assessment as highly reliable within the available symbolic evidence.",
    "medium": "The system considers this assessment plausible but still caveat-sensitive.",
    "low": "The system considers this assessment tentative and sensitive to uncertainty in the available evidence.",
}

INTERPRETATION_TEXT = {
    "robust": "The interpretation is treated as robust.",
    "qualified": "The interpretation is qualified by contextual limitations.",
    "cautious": "The interpretation is cautious because the available support is limited or caveat-heavy.",
    "tentative": "The interpretation remains tentative and should be read as an early warning rather than a definitive conclusion.",
}


def humanize(token: str) -> str:
    return token.replace("_", " ")


def title_case(token: str) -> str:
    return humanize(token).title()


def join_phrases(items: list[str]) -> str:
    if not items:
        return "none"
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def join_sentences(parts: list[str]) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def evidence_phrase(evidence_items: list[str]) -> str:
    return join_phrases([EVIDENCE_LABELS.get(item, humanize(item)) for item in evidence_items])


def confidence_phrase(confidence: str) -> str:
    return {
        "high": "high confidence",
        "medium": "moderate confidence",
        "low": "low confidence",
    }.get(confidence, f"{humanize(confidence)} confidence")


def severity_phrase(severity: str, hazard_type: str) -> str:
    return f"{humanize(severity)} {humanize(hazard_type)} event"


def caveat_phrase_list(caveat_items: list[str]) -> str:
    return join_phrases([CAVEAT_LIST_TEXT.get(item, humanize(item)) for item in caveat_items])


def interpretation_sentence(interpretation_mode: str) -> str:
    return INTERPRETATION_TEXT.get(
        interpretation_mode,
        f"The interpretation mode is {humanize(interpretation_mode)}.",
    )


def confidence_rationale(assessment: dict, evidence: dict) -> str:
    claim = assessment["claim_label"]
    confidence = assessment["fusion_confidence"]
    support_level = assessment.get("support_level", "unknown")
    caveat_items = evidence["caveat_items"]
    evidence_items = evidence["evidence_items"]

    if assessment.get("conclusion_status", "hazard_assessed") == "inconclusive":
        return (
            "Confidence remains low because the available indicators did not form a coherent "
            "hazard pattern strong enough to support a firm conclusion."
        )

    if confidence == "high":
        if support_level == "strong" or "strong_multisignal" in claim or len(evidence_items) >= 3:
            return (
                "Confidence is high because multiple independent EO indicators agree and no "
                "major caveat substantially weakens the interpretation."
            )
        return (
            "Confidence is high because the available indicators point in the same direction "
            "without a strong contradictory signal."
        )

    if confidence == "medium":
        if support_level == "moderate" and not caveat_items:
            return (
                "Confidence is moderate because the evidence is coherent across multiple signals, "
                "but not strong enough to be treated as a high-support case."
            )
        if caveat_items:
            return (
                "Confidence is moderate because the main indicators support the assessment, "
                f"but the reading is still qualified by {caveat_phrase_list(caveat_items)}."
            )
        return (
            "Confidence is moderate because the symbolic evidence is coherent, but not strong "
            "enough to be treated as fully robust."
        )

    if caveat_items:
        return (
            "Confidence is low because the evidence is weak, partial, or caveat-heavy, and is "
            f"further qualified by {caveat_phrase_list(caveat_items)}."
        )
    return (
        "Confidence is low because the available evidence does not provide enough support for a "
        "stronger conclusion."
    )


def is_inconclusive_assessment(assessment: dict) -> bool:
    return assessment.get("conclusion_status", "hazard_assessed") == "inconclusive"


def inconclusive_summary(event: dict, assessment: dict) -> str:
    return (
        f"{event['event_name']} could not be assigned a reliable {event['hazard_type']} severity "
        f"from the available evidence. The system keeps the case at {confidence_phrase(assessment['fusion_confidence'])} "
        "and treats it as an inconclusive signal rather than a confirmed hazard conclusion."
    )


def inconclusive_what_happened(event: dict) -> str:
    return (
        f"The event is located in {event['region']['name']}, {event['country']['name']}. "
        f"The system did not find enough coherent {humanize(event['hazard_type'])}-related evidence "
        "to reach a firm conclusion."
    )


def inconclusive_evidence_text(event: dict, evidence: dict, assessment: dict) -> str:
    if evidence["evidence_items"]:
        return (
            f"{CLAIM_TEXT.get(assessment['claim_label'], 'The available evidence remains inconclusive.')} "
            f"The partial reasoning path considered {evidence_phrase(evidence['evidence_items'])}, "
            "but those indicators were not sufficient to support a firm conclusion."
        )
    return (
        f"{CLAIM_TEXT.get(assessment['claim_label'], 'The available evidence remains inconclusive.')} "
        f"No supporting {humanize(event['hazard_type'])}-specific indicators crossed the thresholds "
        "required for a reliable conclusion."
    )


def caveat_sentence(primary_caveat: str, caveat_items: list[str]) -> str:
    if not caveat_items:
        return "No major caveats were attached to this assessment."

    primary_text = CAVEAT_TEXT.get(primary_caveat, humanize(primary_caveat))
    remaining_items = [item for item in caveat_items if item != primary_caveat]

    if not remaining_items:
        return f"The main caveat is that {primary_text}."

    caveat_phrases = [CAVEAT_LIST_TEXT.get(item, humanize(item)) for item in remaining_items]
    return (
        f"The main caveat is that {primary_text}. Additional limitations include "
        f"{join_phrases(caveat_phrases)}."
    )


def clarification_sentence(payload: dict) -> str:
    clarification = payload["clarification"]
    evidence = payload["evidence"]

    if clarification["clarification_status"] == "no_clarification":
        return (
            "No second-pass clarification was required because the first-pass specialist "
            "assessment was considered sufficient."
        )

    limitation = CAVEAT_TEXT.get(
        clarification["primary_limitation"],
        humanize(clarification["primary_limitation"]),
    )
    strongest_raw = evidence.get("strongest_evidence", "none")
    strongest = (
        "no single strongest evidence item"
        if not strongest_raw or strongest_raw == "none"
        else EVIDENCE_LABELS.get(strongest_raw, humanize(strongest_raw))
    )
    alternative = ALTERNATIVE_CLAIM_TEXT.get(
        clarification["alternative_claim"],
        humanize(clarification["alternative_claim"]),
    )
    return (
        "A second-pass clarification was requested. "
        f"The specialist identified the main limitation as {limitation}. "
        f"The specialist retained {strongest} as the strongest supporting evidence, "
        f"and noted {alternative} as the closest alternative interpretation."
    )


def provenance_sentence(provenance: dict) -> str:
    agent = humanize(provenance["source_agent"])
    rule = provenance["rule_label"]
    return (
        f"This assessment was produced by the {agent} and grounded in the symbolic "
        f"rule `{rule}`."
    )


def user_assessment_sentence(payload: dict) -> str | None:
    user_assessment = payload.get("user_assessment", {})
    provided = user_assessment.get("user_assessment", "none")
    alignment = user_assessment.get("user_assessment_alignment", "not_provided")
    inferred = payload["assessment"]["severity"]
    assessment = payload["assessment"]
    claim_label = assessment["claim_label"]
    hazard_type = payload["event"]["hazard_type"]

    if provided in {"none", "", None} or alignment == "not_provided":
        return None

    if alignment == "matches":
        return (
            f"A user-provided severity of {humanize(provided)} was supplied, and it matches "
            "the system's inferred severity."
        )

    primary_caveat = payload["evidence"]["primary_caveat"]
    caveat_clause = ""
    if primary_caveat != "no_major_caveat":
        caveat_clause = (
            f" The interpretation is additionally qualified by {CAVEAT_TEXT.get(primary_caveat, humanize(primary_caveat))}."
        )

    if is_inconclusive_assessment(assessment):
        return (
            f"A user-provided severity of {humanize(provided)} was supplied, but the system could not reach "
            f"a reliable {humanize(hazard_type)} severity conclusion. "
            f"The available reasoning path did not provide enough coherent support to confirm that expectation."
            f"{caveat_clause}"
        )

    return (
        f"A user-provided severity of {humanize(provided)} was supplied, but the system inferred "
        f"a {severity_phrase(inferred, hazard_type)}. The symbolic evidence supported the inferred severity rather than the user-provided one."
        f"{caveat_clause}"
    )


def build_report_text(payload: dict) -> str:
    event = payload["event"]
    assessment = payload["assessment"]
    evidence = payload["evidence"]
    provenance = payload["provenance"]
    clarification = payload["clarification"]
    user_assessment_text = user_assessment_sentence(payload)
    inconclusive = is_inconclusive_assessment(assessment)

    if inconclusive:
        summary = inconclusive_summary(event, assessment)
        what_happened = inconclusive_what_happened(event)
    else:
        summary = (
            f"{event['event_name']} is assessed as a {severity_phrase(assessment['severity'], event['hazard_type'])} "
            f"with {confidence_phrase(assessment['fusion_confidence'])}."
        )
        what_happened = (
            f"The event is located in {event['region']['name']}, {event['country']['name']}. "
            f"The system classifies it as a {severity_phrase(assessment['severity'], event['hazard_type'])}."
        )
    concern_expl = CONCERN_TEXT.get(assessment["concern_level"], "")
    profile_expl = CASE_PROFILE_TEXT.get(assessment["case_profile"], "")
    if assessment["case_profile"] in CASE_PROFILE_TEXT:
        concern_expl = ""
    if (
        (assessment["concern_level"], assessment["case_profile"])
        in {
            ("watch", "watch_case"),
            ("high", "high_priority_event"),
            ("critical", "critical_concern_case"),
        }
    ) or (profile_expl and profile_expl == concern_expl):
        profile_expl = ""
    assessment_text = join_sentences(
        [
            f"The integrated concern level is {humanize(assessment['concern_level'])}, and the case "
            f"profile is classified as a {humanize(assessment['case_profile'])}.",
            CONFIDENCE_TEXT.get(assessment["fusion_confidence"], ""),
            confidence_rationale(assessment, evidence),
            interpretation_sentence(assessment["interpretation_mode"]),
            concern_expl,
            profile_expl,
        ]
    )
    if inconclusive:
        evidence_text = inconclusive_evidence_text(event, evidence, assessment)
    else:
        evidence_text = (
            f"{CLAIM_TEXT.get(assessment['claim_label'], 'The assessment is grounded in the available symbolic evidence.')} "
            f"The reasoning path relies on {evidence_phrase(evidence['evidence_items'])}."
        )
    caveats_text = caveat_sentence(evidence["primary_caveat"], evidence["caveat_items"])
    clarification_text = clarification_sentence(payload)
    provenance_text = provenance_sentence(provenance)
    symbolic = [
        f"- Conclusion status: {assessment.get('conclusion_status', 'hazard_assessed')}",
        f"- Severity label: {assessment['severity']}",
        f"- Support level: {assessment.get('support_level', 'not_available')}",
        f"- Claim label: {assessment['claim_label']}",
        f"- Primary caveat: {evidence['primary_caveat']}",
        f"- Clarification status: {clarification['clarification_status']}",
        f"- Source agent: {provenance['source_agent']}",
        f"- Rule label: {provenance['rule_label']}",
    ]

    sections = [
        f"EO2Explain Event Report: {event['event_name']}",
        f"Location: {event['region']['name']}, {event['country']['name']}",
        f"Hazard Type: {title_case(event['hazard_type'])}",
        "",
        "Summary",
        summary,
        "",
        "What Happened",
        what_happened,
        "",
        "Assessment",
        assessment_text,
        "",
    ]

    if user_assessment_text:
        sections.extend(
            [
                "User Assessment",
                user_assessment_text,
                "",
            ]
        )

    sections.extend([
        "Supporting Evidence",
        evidence_text,
        "",
        "Caveats And Limitations",
        caveats_text,
        "",
        "Clarification",
        clarification_text,
        "",
        "Provenance",
        provenance_text,
        "",
        "Symbolic Details",
        "\n".join(symbolic),
    ])

    return "\n".join(sections) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate raw report text files from transformed semantic JSON payloads."
    )
    parser.add_argument(
        "--input-dir",
        default="outputs/transformed",
        help="Directory containing transformed semantic JSON files.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/reports",
        help="Directory where raw text reports will be written.",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.is_absolute():
        input_dir = PROJECT_ROOT / input_dir

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir

    if not input_dir.exists():
        raise SystemExit(f"Input directory does not exist: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    for payload in load_payloads(input_dir):
        report_path = output_dir / f"{payload['event_id']}.txt"
        report_path.write_text(build_report_text(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
