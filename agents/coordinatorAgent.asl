{ include("beliefs/events.asl") }
{ include("beliefs/indicators.asl") }
// Reference labels are included only for post-hoc evaluation logging, not for
// live coordination or runtime decision making.
{ include("beliefs/reference_labels.asl") }

!start.

// The coordinator launches one assessment request per event and waits for the
// responsible hazard agent to return a structured symbolic judgment.
+!start <-
    .print("coordinator agent started");
    .findall(E, event(E), Events);  // Gather all events at startup to dispatch assessment requests.
    !dispatch_events(Events).

+!dispatch_events([]) <-
    .print("coordinator agent dispatched all assessment requests").

+!dispatch_events([E|Rest]) <-
    ?agent_responsible(E, Agent);
    +pending_assessment(E);
    .send(Agent, achieve, assess_event(E, coordinator_agent)); // sends an achieve message to the responsible agent for each event to start the assessment process.
    !dispatch_events(Rest).
    
+hazard_assessment(E, Hazard, Severity, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel)[source(SourceAgent)] :
    pending_assessment(E) <-
    -pending_assessment(E);
    +hazard_result(E, Hazard, Severity, HazardConfidence, ClaimLabel, PrimaryCaveat, SourceAgent);
    +hazard_trace(E, SourceAgent, RuleLabel, EvidenceList, CaveatList);
    +claim_support(E, hazard_classification, SourceAgent, EvidenceList);
    +claim_support(E, severity_classification, SourceAgent, EvidenceList);
    +claim_support(E, confidence_assessment, SourceAgent, CaveatList);
    !handle_post_assessment(E, Hazard, Severity, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent).

// The coordinator only escalates cases that remain uncertain after the first pass.
+!handle_post_assessment(E, Hazard, Severity, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent) :
    clarification_required(HazardConfidence, PrimaryCaveat) <-
    +pending_clarification(E);
    +clarification_context(E, Hazard, Severity, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent);
    .send(SourceAgent, achieve, clarify_assessment(E, ClaimLabel, PrimaryCaveat, coordinator_agent)).

+!handle_post_assessment(E, Hazard, Severity, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent) <-
    !fuse_case(E, Hazard, Severity, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent, no_clarification, no_additional_limitation, none, no_alternative_claim).

+clarification_result(E, ClaimLabel, PrimaryLimitation, StrongestEvidence, AlternativeClaim, ClarificationStatus)[source(SourceAgent)] :
    pending_clarification(E) &
    clarification_context(E, Hazard, Severity, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent) <-
    -pending_clarification(E);
    -clarification_context(E, Hazard, Severity, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent);
    +clarification_detail(E, ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim, SourceAgent);
    +claim_support(E, clarification_assessment, SourceAgent, [PrimaryLimitation, StrongestEvidence, AlternativeClaim]);
    !fuse_case(E, Hazard, Severity, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent, ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim).

// Fusion happens here: hazard output is combined with exposure and caveat-aware
// confidence handling to produce the integrated case used by the explanation agent.
+!fuse_case(E, Hazard, Severity, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent, ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim) <-
    ?population_exposure_class(E, ExposureClass);
    ?concern_level(Severity, ExposureClass, ConcernLevel);
    ?fusion_confidence(Severity, HazardConfidence, PrimaryCaveat, FusionConfidence);
    ?interpretation_mode(FusionConfidence, PrimaryCaveat, InterpretationMode);
    ?case_profile(ConcernLevel, FusionConfidence, InterpretationMode, Profile);
    +integrated_case(E, Hazard, Severity, ClaimLabel, ExposureClass, ConcernLevel, FusionConfidence, InterpretationMode, Profile, SourceAgent, ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim);
    +claim_support(E, concern_classification, coordinator_agent, [population_exposure_class, severity_classification]);
    +claim_support(E, fusion_confidence, coordinator_agent, [confidence_assessment, PrimaryCaveat]);
    +claim_support(E, case_profile, coordinator_agent, [concern_classification, fusion_confidence]);
    .send(explanation_agent, achieve, build_explanation(E, Hazard, Severity, ClaimLabel, ExposureClass, ConcernLevel, FusionConfidence, InterpretationMode, Profile, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent, ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim)).

+semantic_explanation(E, EventFrame, AssessmentFrame, EvidenceFrame, ClarificationFrame, ProvenanceFrame, HeadlineFrame, debug_text(short_headline(DebugHeadline), short_summary(DebugSummary)), ExplanationTrace)[source(explanation_agent)] :
    integrated_case(E, Hazard, Severity, ClaimLabel, ExposureClass, ConcernLevel, FusionConfidence, InterpretationMode, Profile, SourceAgent, ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim) <-
    +final_explanation_payload(E, semantic_explanation(E, EventFrame, AssessmentFrame, EvidenceFrame, ClarificationFrame, ProvenanceFrame, HeadlineFrame, debug_text(short_headline(DebugHeadline), short_summary(DebugSummary)), ExplanationTrace));
    +claim_support(E, explanation_packaging, explanation_agent, [ClaimLabel, FusionConfidence, ExplanationTrace]);
    ?reference_hazard(E, ReferenceHazard);
    ?reference_severity(E, ReferenceSeverity);
    ?reference_confidence(E, ReferenceConfidence);
    !match_label(Hazard, ReferenceHazard, HazardMatch);
    !match_label(Severity, ReferenceSeverity, SeverityMatch);
    !match_label(FusionConfidence, ReferenceConfidence, ConfidenceMatch);
    .concat("-----\nEvent: ", E, Block1);
    .concat(Block1, "\nSemantic explanation payload ready", Block2);
    .concat(Block2, "\n\n[Debug headline] ", Block3);
    .concat(Block3, DebugHeadline, Block4);
    .concat(Block4, "\n[Debug summary] ", Block5);
    .concat(Block5, DebugSummary, Block6);
    .concat(Block6, "\n\n[Event frame]\n  ", Block7);
    .concat(Block7, EventFrame, Block8);
    .concat(Block8, "\n[Assessment frame]\n  ", Block9);
    .concat(Block9, AssessmentFrame, Block10);
    .concat(Block10, "\n[Evidence frame]\n  ", Block11);
    .concat(Block11, EvidenceFrame, Block12);
    .concat(Block12, "\n[Clarification frame]\n  ", Block13);
    .concat(Block13, ClarificationFrame, Block14);
    .concat(Block14, "\n[Provenance frame]\n  ", Block15);
    .concat(Block15, ProvenanceFrame, Block16);
    .concat(Block16, "\n[Headline frame]\n  ", Block17);
    .concat(Block17, HeadlineFrame, Block18);
    .concat(Block18, "\n[Trace]\n  ", Block19);
    .concat(Block19, ExplanationTrace, Block20);
    .concat(Block20, "\n\n[Reference alignment] hazard=", Block21);
    .concat(Block21, HazardMatch, Block22);
    .concat(Block22, ", severity=", Block23);
    .concat(Block23, SeverityMatch, Block24);
    .concat(Block24, ", confidence=", Block25);
    .concat(Block25, ConfidenceMatch, FullBlock);
    .print(FullBlock).

+!match_label(Value, Value, match) <- true.
+!match_label(Value, Reference, differs) : Value \== Reference <- true.

clarification_required(low, _).
clarification_required(medium, burn_signal_weak).
clarification_required(medium, weak_water_signal).
clarification_required(medium, residual_observation_window).
clarification_required(medium, limited_multisignal_support).

// These tables keep the fusion logic readable and easy to tune against the reference set.
critical_concern(severe, high).
high_concern(severe, medium).
high_concern(severe, low).
high_concern(moderate, high).
elevated_concern(moderate, medium).
moderate_concern(moderate, low).
elevated_concern(mild, high).
guarded_concern(mild, medium).
watch_concern(mild, low).

concern_level(Severity, ExposureClass, critical) :-
    critical_concern(Severity, ExposureClass).
concern_level(Severity, ExposureClass, high) :-
    high_concern(Severity, ExposureClass).
concern_level(Severity, ExposureClass, elevated) :-
    elevated_concern(Severity, ExposureClass).
concern_level(Severity, ExposureClass, moderate) :-
    moderate_concern(Severity, ExposureClass).
concern_level(Severity, ExposureClass, guarded) :-
    guarded_concern(Severity, ExposureClass).
concern_level(Severity, ExposureClass, watch) :-
    watch_concern(Severity, ExposureClass).

fusion_confidence(_, low, _, low).
fusion_confidence(_, medium, _, medium).
fusion_confidence(mild, high, residual_observation_window, medium).
fusion_confidence(_, high, burn_signal_weak, medium).
fusion_confidence(_, high, weak_water_signal, medium).
fusion_confidence(_, high, limited_multisignal_support, medium).
fusion_confidence(_, high, _, high).

interpretation_mode(high, no_major_caveat, robust).
interpretation_mode(high, _, qualified).
interpretation_mode(medium, _, cautious).
interpretation_mode(low, _, tentative).

case_profile(critical, high, _, critical_concern_case).
case_profile(high, high, _, high_priority_event).
case_profile(high, medium, _, confidence_limited_priority_event).
case_profile(elevated, high, _, elevated_priority_event).
case_profile(elevated, medium, _, cautious_monitoring_case).
case_profile(moderate, _, _, monitoring_case).
case_profile(guarded, _, _, guarded_monitoring_case).
case_profile(watch, _, _, watch_case).
