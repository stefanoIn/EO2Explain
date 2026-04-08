{ include("beliefs/events.asl") }

!start.

+!start <-
    .print("[explanation_agent] started").

// The explanation agent  acts as a semantic packaging layer between the
// Jason reasoning system and a future external Python/OWL reporting pipeline.
// It exports a structured explanation payload plus a compact debug summary.
+!build_explanation(E, Hazard, Severity, ClaimLabel, ExposureClass, ConcernLevel, FusionConfidence, InterpretationMode, Profile, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent, ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim) <-
    ?name(E, EventName);
    ?country(E, CountryId);
    ?country_name(CountryId, CountryName);
    ?region(E, RegionId);
    ?region_name(RegionId, RegionName);
    !compose_debug_headline(EventName, Severity, Hazard, FusionConfidence, DebugHeadline);
    !compose_debug_summary(ClaimLabel, ConcernLevel, Profile, PrimaryCaveat, ClarificationStatus, StrongestEvidence, AlternativeClaim, DebugSummary);
    .print("[explanation_agent] packaged semantic explanation for ", E, ": headline=", DebugHeadline);
    .send(coordinator_agent, tell,
        semantic_explanation(
            E,
            event_frame(
                event_id(E),
                event_name(EventName),
                hazard_type(Hazard),
                country(CountryId, CountryName),
                region(RegionId, RegionName)
            ),
            assessment_frame(
                severity(Severity),
                claim_label(ClaimLabel),
                fusion_confidence(FusionConfidence),
                concern_level(ConcernLevel),
                interpretation_mode(InterpretationMode),
                case_profile(Profile),
                exposure_class(ExposureClass)
            ),
            evidence_frame(
                primary_caveat(PrimaryCaveat),
                evidence_items(EvidenceList),
                caveat_items(CaveatList),
                strongest_evidence(StrongestEvidence)
            ),
            clarification_frame(
                clarification_status(ClarificationStatus),
                primary_limitation(PrimaryLimitation),
                alternative_claim(AlternativeClaim)
            ),
            provenance_frame(
                source_agent(SourceAgent),
                rule_label(RuleLabel)
            ),
            headline_frame(
                event_name(EventName),
                region_name(RegionName),
                country_name(CountryName),
                severity(Severity),
                hazard_type(Hazard),
                fusion_confidence(FusionConfidence)
            ),
            debug_text(
                short_headline(DebugHeadline),
                short_summary(DebugSummary)
            ),
            explanation_trace(
                SourceAgent,
                RuleLabel,
                ClaimLabel,
                EvidenceList,
                CaveatList,
                clarification_trace(
                    ClarificationStatus,
                    PrimaryLimitation,
                    StrongestEvidence,
                    AlternativeClaim
                )
            )
        )
    ).

// Debug strings are intentionally compact. They are useful inside Jason logs,
// but they are not intended to be the final user-facing explanation.
+!compose_debug_headline(EventName, Severity, Hazard, FusionConfidence, Headline) <-
    .concat(EventName, " | ", Part1);
    .concat(Part1, Severity, Part2);
    .concat(Part2, " ", Part3);
    .concat(Part3, Hazard, Part4);
    .concat(Part4, " | ", Part5);
    .concat(Part5, FusionConfidence, Headline).

+!compose_debug_summary(ClaimLabel, ConcernLevel, Profile, PrimaryCaveat, ClarificationStatus, StrongestEvidence, AlternativeClaim, Summary) <-
    .concat("claim=", ClaimLabel, Part1);
    .concat(Part1, "; concern=", Part2);
    .concat(Part2, ConcernLevel, Part3);
    .concat(Part3, "; profile=", Part4);
    .concat(Part4, Profile, Part5);
    .concat(Part5, "; caveat=", Part6);
    .concat(Part6, PrimaryCaveat, Part7);
    .concat(Part7, "; clarification=", Part8);
    .concat(Part8, ClarificationStatus, Part9);
    .concat(Part9, "; strongest_evidence=", Part10);
    .concat(Part10, StrongestEvidence, Part11);
    .concat(Part11, "; alternative_claim=", Part12);
    .concat(Part12, AlternativeClaim, Summary).
