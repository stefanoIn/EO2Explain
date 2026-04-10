#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

if "." not in sys.path:
    sys.path.insert(0, ".")

from nlp.loader.load_payloads import load_payloads


EVIDENCE_LABELS = {
    "water_increase_pct": "surface-water increase",
    "newly_flooded_area_pct": "newly flooded area",
    "ndwi_change": "NDWI change",
    "vegetation_loss_pct": "vegetation loss",
    "burned_area_pct": "burned-area extent",
    "mean_dnbr": "mean dNBR burn severity",
}

ALTERNATIVE_CLAIM_TEXT = {
    "inconclusive_fire_signal": "an inconclusive fire signal",
    "inconclusive_water_signal": "an inconclusive water signal",
    "no_alternative_claim": "no alternative claim",
}

CAVEAT_TEXT = {
    "late_observation": "post-event imagery was acquired late, so peak impact may no longer be fully visible",
    "possible_underestimation": "the measured footprint may underestimate the real extent of the event",
    "weak_water_signal": "the water signal is weak and must be interpreted cautiously",
    "burn_signal_weak": "the burn signal is weak or partly contradictory",
    "timeline_uncertain": "the event timeline mixes confirmed and approximate temporal information",
    "coarse_timeline": "the event timing is only coarsely constrained",
    "residual_observation_window": "the observed footprint likely reflects residual conditions rather than peak impact",
    "limited_multisignal_support": "the interpretation is not supported by a full set of corroborating signals",
}

CAVEAT_LIST_TEXT = {
    "late_observation": "late image acquisition",
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
    "moderate": "This means the event should be monitored as a moderate concern.",
    "guarded": "This means the event should be handled cautiously because the situation remains uncertain or limited in scope.",
    "watch": "This means the event is currently in watch status and should be monitored for possible escalation.",
}

CASE_PROFILE_TEXT = {
    "critical_concern_case": "This indicates a critical situation requiring immediate attention.",
    "high_priority_event": "This indicates a high-priority situation that should remain under close observation.",
    "monitoring_case": "This indicates a situation that should remain under routine monitoring.",
    "guarded_monitoring_case": "This indicates a situation that should be monitored cautiously due to remaining uncertainty.",
    "watch_case": "This indicates a watch-level situation that should be monitored for possible escalation.",
}

CLAIM_TEXT = {
    "strong_multisignal_flooding": "The flood assessment is supported by a strong multi-signal pattern combining water expansion, newly flooded area, and spectral water change.",
    "residual_flood_signal": "The system detects a residual flood footprint, suggesting that flood impact remains visible even though the image may have missed peak conditions.",
    "coherent_fire_damage": "The wildfire assessment is supported by consistent vegetation-loss and burned-area evidence.",
    "spectral_extent_fire_damage": "The wildfire assessment is supported by burn extent together with spectral burn-severity evidence.",
    "mixed_fire_damage": "Wildfire damage is still indicated, but the spectral burn evidence is mixed relative to the vegetation-loss and burned-area signals.",
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


def interpretation_sentence(interpretation_mode: str) -> str:
    return INTERPRETATION_TEXT.get(
        interpretation_mode,
        f"The interpretation mode is {humanize(interpretation_mode)}.",
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


def build_report_text(payload: dict) -> str:
    event = payload["event"]
    assessment = payload["assessment"]
    evidence = payload["evidence"]
    provenance = payload["provenance"]
    clarification = payload["clarification"]

    summary = (
        f"{event['event_name']} is assessed as a {assessment['severity']} {event['hazard_type']} "
        f"event with {confidence_phrase(assessment['fusion_confidence'])}, based on the available observational evidence."
    )
    what_happened = (
        f"The event is located in {event['region']['name']}, {event['country']['name']}. "
        f"The system interprets it as a {humanize(assessment['severity'])} {humanize(event['hazard_type'])} event."
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
            interpretation_sentence(assessment["interpretation_mode"]),
            concern_expl,
            profile_expl,
        ]
    )
    evidence_text = (
        f"{CLAIM_TEXT.get(assessment['claim_label'], 'The assessment is grounded in the available symbolic evidence.')} "
        f"The reasoning path relies on {evidence_phrase(evidence['evidence_items'])}."
    )
    caveats_text = caveat_sentence(evidence["primary_caveat"], evidence["caveat_items"])
    clarification_text = clarification_sentence(payload)
    provenance_text = provenance_sentence(provenance)
    symbolic = [
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
    ]

    return "\n".join(sections) + "\n"


def main() -> None:
    output_dir = Path("outputs/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    for payload in load_payloads():
        report_path = output_dir / f"{payload['event_id']}.txt"
        report_path.write_text(build_report_text(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
