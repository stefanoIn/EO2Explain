{ include("./beliefs/events.asl") }

!start.

+!start <-
    .print("EXPLANATION AGENT started");
    .custom.trace_line("EXPLANATION AGENT", "Started explanation packager.").

// The explanation agent  acts as a semantic packaging layer between the
// Jason reasoning system and a future external Python/OWL reporting pipeline.
// It exports a structured explanation payload plus a compact debug summary.
+!build_explanation(E, Hazard, Severity, SupportLevel, ConclusionStatus, ClaimLabel, ExposureClass, ConcernLevel, FusionConfidence, InterpretationMode, Profile, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent, ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim, UserAssessment, UserAssessmentAlignment) <-
    ?name(E, EventName);
    ?country(E, CountryId);
    ?country_name(CountryId, CountryName);
    ?region(E, RegionId);
    ?region_name(RegionId, RegionName);
    !compose_debug_headline(EventName, Severity, SupportLevel, Hazard, FusionConfidence, DebugHeadline);
    !compose_debug_summary(SupportLevel, ClaimLabel, ConcernLevel, Profile, PrimaryCaveat, ClarificationStatus, StrongestEvidence, AlternativeClaim, DebugSummary);
    .print("packaged payload for ", E, " -> ", DebugHeadline);
    .concat("Packaging explanation for ", E, Trace1);
    .concat(Trace1, " with headline ", Trace2);
    .concat(Trace2, DebugHeadline, Trace3);
    .concat(Trace3, ".", Trace4);
    .custom.trace_line("EXPLANATION AGENT", Trace4);
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
                support_level(SupportLevel),
                conclusion_status(ConclusionStatus),
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
            user_assessment_frame(
                user_assessment(UserAssessment),
                user_assessment_alignment(UserAssessmentAlignment)
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
                support_level(SupportLevel),
                conclusion_status(ConclusionStatus),
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
+!compose_debug_headline(EventName, Severity, SupportLevel, Hazard, FusionConfidence, Headline) <-
    .concat(EventName, " | ", Part1);
    .concat(Part1, Severity, Part2);
    .concat(Part2, " ", Part3);
    .concat(Part3, Hazard, Part4);
    .concat(Part4, " | ", Part5);
    .concat(Part5, SupportLevel, Part6);
    .concat(Part6, " support | ", Part7);
    .concat(Part7, FusionConfidence, Part8);
    .concat(Part8, " confidence", Headline).

+!compose_debug_summary(SupportLevel, ClaimLabel, ConcernLevel, Profile, PrimaryCaveat, ClarificationStatus, StrongestEvidence, AlternativeClaim, Summary) <-
    .concat("support=", SupportLevel, Part1);
    .concat(Part1, "; claim=", Part2);
    .concat(Part2, ClaimLabel, Part3);
    .concat(Part3, "; concern=", Part4);
    .concat(Part4, ConcernLevel, Part5);
    .concat(Part5, "; profile=", Part6);
    .concat(Part6, Profile, Part7);
    .concat(Part7, "; caveat=", Part8);
    .concat(Part8, PrimaryCaveat, Part9);
    .concat(Part9, "; clarification=", Part10);
    .concat(Part10, ClarificationStatus, Part11);
    .concat(Part11, "; strongest_evidence=", Part12);
    .concat(Part12, StrongestEvidence, Part13);
    .concat(Part13, "; alternative_claim=", Part14);
    .concat(Part14, AlternativeClaim, Summary).
