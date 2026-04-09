#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from nlp.loader.load_payloads import load_payloads


def build_report_text(payload: dict) -> str:
    event = payload["event"]
    assessment = payload["assessment"]
    evidence = payload["evidence"]
    clarification = payload["clarification"]

    return (
        f"Event: {event['event_name']} ({event['country']['name']})\n"
        f"Hazard: {event['hazard_type']}\n"
        f"Severity: {assessment['severity']}\n"
        f"Confidence: {assessment['fusion_confidence']}\n"
        f"Claim: {assessment['claim_label']}\n"
        f"Primary caveat: {evidence['primary_caveat']}\n"
        f"Evidence: {', '.join(evidence['evidence_items'])}\n"
        f"Clarification: {clarification['clarification_status']}\n"
    )


def main() -> None:
    output_dir = Path("outputs/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    for payload in load_payloads():
        report_path = output_dir / f"{payload['event_id']}.txt"
        report_path.write_text(build_report_text(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
