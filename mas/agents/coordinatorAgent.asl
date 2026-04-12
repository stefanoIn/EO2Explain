{ include("./beliefs/events.asl") }
{ include("./beliefs/indicators.asl") }
{ include("./beliefs/population_exposure.asl") }
{ include("./beliefs/user_inputs.asl") }

!start.

// The coordinator launches one assessment request per event and waits for the
// responsible hazard agent to return a structured symbolic judgment.
+!start <-
    .print("COORDINATOR AGENT started");
    .custom.trace_line("COORDINATOR AGENT", "Started coordinator workflow.");
    .findall(E, event(E), Events);  // Gather all events at startup to dispatch assessment requests.
    !dispatch_events(Events).

+!dispatch_events([]) <-
    .print("all assessment requests dispatched");
    .custom.trace_line("COORDINATOR AGENT", "All assessment requests dispatched.").

+!dispatch_events([E|Rest]) <-
    ?agent_responsible(E, Agent);
    +pending_assessment(E);
    .concat("Requesting assessment for ", E, Msg1);
    .concat(Msg1, " from ", Msg2);
    .concat(Msg2, Agent, Msg3);
    .concat(Msg3, ".", Msg4);
    .custom.trace_line("COORDINATOR AGENT", Msg4);
    .send(Agent, achieve, assess_event(E, coordinator_agent)); // sends an achieve message to the responsible agent for each event to start the assessment process.
    !dispatch_events(Rest).
    
+hazard_assessment(E, Hazard, Severity, SupportLevel, ConclusionStatus, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel)[source(SourceAgent)] :
    pending_assessment(E) <-
    -pending_assessment(E);
    +hazard_result(E, Hazard, Severity, SupportLevel, ConclusionStatus, HazardConfidence, ClaimLabel, PrimaryCaveat, SourceAgent);
    +hazard_trace(E, SourceAgent, RuleLabel, EvidenceList, CaveatList);
    +claim_support(E, hazard_classification, SourceAgent, EvidenceList);
    +claim_support(E, severity_classification, SourceAgent, EvidenceList);
    +claim_support(E, confidence_assessment, SourceAgent, CaveatList);
    +claim_support(E, support_assessment, SourceAgent, [SupportLevel, ClaimLabel]);
    .concat("Received first-pass assessment for ", E, Msg1);
    .concat(Msg1, " from ", Msg2);
    .concat(Msg2, SourceAgent, Msg3);
    .concat(Msg3, " with support=", Msg4);
    .concat(Msg4, SupportLevel, Msg5);
    .concat(Msg5, ", severity=", Msg6);
    .concat(Msg6, Severity, Msg7);
    .concat(Msg7, ", status=", Msg8);
    .concat(Msg8, ConclusionStatus, Msg9);
    .concat(Msg9, ", confidence=", Msg10);
    .concat(Msg10, HazardConfidence, Msg11);
    .concat(Msg11, ".", Msg12);
    .custom.trace_line("COORDINATOR AGENT", Msg12);
    !handle_post_assessment(E, Hazard, Severity, SupportLevel, ConclusionStatus, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent).

// The coordinator only escalates cases that remain uncertain after the first pass.
+!handle_post_assessment(E, Hazard, Severity, SupportLevel, ConclusionStatus, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent) :
    clarification_required(HazardConfidence, PrimaryCaveat) <-
    +pending_clarification(E);
    +clarification_context(E, Hazard, Severity, SupportLevel, ConclusionStatus, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent);
    .print("clarification requested for ", E, " -> confidence=", HazardConfidence, ", caveat=", PrimaryCaveat, ", source=", SourceAgent);
    .concat("Requesting clarification for ", E, Msg1);
    .concat(Msg1, " from ", Msg2);
    .concat(Msg2, SourceAgent, Msg3);
    .concat(Msg3, " because caveat=", Msg4);
    .concat(Msg4, PrimaryCaveat, Msg5);
    .concat(Msg5, ".", Msg6);
    .custom.trace_line("COORDINATOR AGENT", Msg6);
    .send(SourceAgent, achieve, clarify_assessment(E, ClaimLabel, PrimaryCaveat, coordinator_agent)).

+!handle_post_assessment(E, Hazard, Severity, SupportLevel, ConclusionStatus, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent) <-
    !fuse_case(E, Hazard, Severity, SupportLevel, ConclusionStatus, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent, no_clarification, no_additional_limitation, none, no_alternative_claim).

+clarification_result(E, ClaimLabel, PrimaryLimitation, StrongestEvidence, AlternativeClaim, ClarificationStatus)[source(SourceAgent)] :
    pending_clarification(E) &
    clarification_context(E, Hazard, Severity, SupportLevel, ConclusionStatus, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent) <-
    -pending_clarification(E);
    -clarification_context(E, Hazard, Severity, SupportLevel, ConclusionStatus, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent);
    +clarification_detail(E, ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim, SourceAgent);
    +claim_support(E, clarification_assessment, SourceAgent, [PrimaryLimitation, StrongestEvidence, AlternativeClaim]);
    .concat("Received clarification for ", E, Msg1);
    .concat(Msg1, " from ", Msg2);
    .concat(Msg2, SourceAgent, Msg3);
    .concat(Msg3, " with limitation=", Msg4);
    .concat(Msg4, PrimaryLimitation, Msg5);
    .concat(Msg5, ".", Msg6);
    .custom.trace_line("COORDINATOR AGENT", Msg6);
    !fuse_case(E, Hazard, Severity, SupportLevel, ConclusionStatus, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent, ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim).

// Fusion happens here: hazard output is combined with exposure and caveat-aware
// confidence handling to produce the integrated case used by the explanation agent.
+!fuse_case(E, Hazard, Severity, SupportLevel, ConclusionStatus, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent, ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim) <-
    ?population_exposure_class(E, ExposureClass);
    ?optional_user_assessment(E, UserAssessment);
    ?severity_user_alignment(Severity, UserAssessment, UserAssessmentAlignment);
    ?concern_level(Severity, ExposureClass, ConcernLevel);
    ?fusion_confidence(Severity, HazardConfidence, PrimaryCaveat, FusionConfidence);
    ?interpretation_mode(FusionConfidence, PrimaryCaveat, InterpretationMode);
    ?case_profile(ConcernLevel, FusionConfidence, InterpretationMode, Profile);
    +integrated_case(E, Hazard, Severity, SupportLevel, ConclusionStatus, ClaimLabel, ExposureClass, ConcernLevel, FusionConfidence, InterpretationMode, Profile, SourceAgent, ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim, UserAssessment, UserAssessmentAlignment);
    +claim_support(E, concern_classification, coordinator_agent, [population_exposure_class, severity_classification]);
    +claim_support(E, fusion_confidence, coordinator_agent, [confidence_assessment, PrimaryCaveat]);
    +claim_support(E, case_profile, coordinator_agent, [concern_classification, fusion_confidence]);
    .concat("Fused final case for ", E, Msg1);
    .concat(Msg1, " with support=", Msg2);
    .concat(Msg2, SupportLevel, Msg3);
    .concat(Msg3, ", concern=", Msg4);
    .concat(Msg4, ConcernLevel, Msg5);
    .concat(Msg5, ", profile=", Msg6);
    .concat(Msg6, Profile, Msg7);
    .concat(Msg7, ".", Msg8);
    .custom.trace_line("COORDINATOR AGENT", Msg8);
    .send(explanation_agent, achieve, build_explanation(E, Hazard, Severity, SupportLevel, ConclusionStatus, ClaimLabel, ExposureClass, ConcernLevel, FusionConfidence, InterpretationMode, Profile, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent, ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim, UserAssessment, UserAssessmentAlignment)).

+semantic_explanation(E, EventFrame, AssessmentFrame, EvidenceFrame, ClarificationFrame, UserAssessmentFrame, ProvenanceFrame, HeadlineFrame, debug_text(short_headline(DebugHeadline), short_summary(DebugSummary)), ExplanationTrace)[source(explanation_agent)] :
    integrated_case(E, Hazard, Severity, SupportLevel, ConclusionStatus, ClaimLabel, ExposureClass, ConcernLevel, FusionConfidence, InterpretationMode, Profile, SourceAgent, ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim, UserAssessment, UserAssessmentAlignment) <-
    ?hazard_trace(E, SourceAgent, RuleLabel, EvidenceList, CaveatList);
    +final_explanation_payload(E, semantic_explanation(E, EventFrame, AssessmentFrame, EvidenceFrame, ClarificationFrame, UserAssessmentFrame, ProvenanceFrame, HeadlineFrame, debug_text(short_headline(DebugHeadline), short_summary(DebugSummary)), ExplanationTrace));
    .custom.export_payload(E, semantic_explanation(E, EventFrame, AssessmentFrame, EvidenceFrame, ClarificationFrame, UserAssessmentFrame, ProvenanceFrame, HeadlineFrame, debug_text(short_headline(DebugHeadline), short_summary(DebugSummary)), ExplanationTrace), ExportPath);
    +payload_export(E, ExportPath);
    +claim_support(E, explanation_packaging, explanation_agent, [ClaimLabel, FusionConfidence, ExplanationTrace]);
    .concat("-----\nEvent: ", E, Block1);
    .concat(Block1, "\nSummary: ", Block2);
    .concat(Block2, DebugHeadline, Block3);
    .concat(Block3, "\nFlow: source=", Block4);
    .concat(Block4, SourceAgent, Block5);
    .concat(Block5, ", clarification=", Block6);
    .concat(Block6, ClarificationStatus, Block7);
    .concat(Block7, "\nAssessment: hazard=", Block8);
    .concat(Block8, Hazard, Block9);
    .concat(Block9, ", severity=", Block10);
    .concat(Block10, Severity, Block11);
    .concat(Block11, ", support=", Block12);
    .concat(Block12, SupportLevel, Block13);
    .concat(Block13, ", status=", Block14);
    .concat(Block14, ConclusionStatus, Block15);
    .concat(Block15, ", confidence=", Block16);
    .concat(Block16, FusionConfidence, Block17);
    .concat(Block17, ", concern=", Block18);
    .concat(Block18, ConcernLevel, Block19);
    .concat(Block19, ", profile=", Block20);
    .concat(Block20, Profile, Block21);
    .concat(Block21, "\nReasoning: claim=", Block22);
    .concat(Block22, ClaimLabel, Block23);
    .concat(Block23, ", rule=", Block24);
    .concat(Block24, RuleLabel, Block25);
    .concat(Block25, "\nEvidence: ", Block26);
    .concat(Block26, EvidenceList, Block27);
    .concat(Block27, "\nCaveats: ", Block28);
    .concat(Block28, CaveatList, Block29);
    .concat(Block29, "\nClarification: limitation=", Block30);
    .concat(Block30, PrimaryLimitation, Block31);
    .concat(Block31, ", strongest_evidence=", Block32);
    .concat(Block32, StrongestEvidence, Block33);
    .concat(Block33, ", alternative_claim=", Block34);
    .concat(Block34, AlternativeClaim, Block35);
    .concat(Block35, "\nUser assessment: severity=", Block36);
    .concat(Block36, UserAssessment, Block37);
    .concat(Block37, ", alignment=", Block38);
    .concat(Block38, UserAssessmentAlignment, Block39);
    .concat(Block39, "\nExport: ", Block40);
    .concat(Block40, ExportPath, FullBlock);
    .print(FullBlock);
    .concat("Exported semantic explanation for ", E, Msg1);
    .concat(Msg1, " to ", Msg2);
    .concat(Msg2, ExportPath, Msg3);
    .concat(Msg3, ".", Msg4);
    .custom.trace_line("COORDINATOR AGENT", Msg4).

optional_user_assessment(E, UserAssessment) :-
    user_assessment(E, UserAssessment).
optional_user_assessment(E, none) :-
    not user_assessment(E, _).

severity_user_alignment(_, none, not_provided).
severity_user_alignment(Severity, Severity, matches).
severity_user_alignment(Severity, UserAssessment, differs) :-
    UserAssessment \== none &
    Severity \== UserAssessment.

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
watch_concern(undetermined, high).
watch_concern(undetermined, medium).
watch_concern(undetermined, low).

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
fusion_confidence(undetermined, _, _, low).
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
