{ include("beliefs/events.asl") }
{ include("beliefs/indicators.asl") }
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
    !fuse_case(E, Hazard, Severity, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent).

// Fusion happens here: hazard output is combined with exposure and caveat-aware
// confidence handling to produce the integrated case used by the explanation agent.
+!fuse_case(E, Hazard, Severity, HazardConfidence, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent) <-
    ?population_exposure_class(E, ExposureClass);
    ?concern_level(Severity, ExposureClass, ConcernLevel);
    ?fusion_confidence(Severity, HazardConfidence, PrimaryCaveat, FusionConfidence);
    ?interpretation_mode(FusionConfidence, PrimaryCaveat, InterpretationMode);
    ?case_profile(ConcernLevel, FusionConfidence, InterpretationMode, Profile);
    +integrated_case(E, Hazard, Severity, ClaimLabel, ExposureClass, ConcernLevel, FusionConfidence, InterpretationMode, Profile, SourceAgent);
    +claim_support(E, concern_classification, coordinator_agent, [population_exposure_class, severity_classification]);
    +claim_support(E, fusion_confidence, coordinator_agent, [confidence_assessment, PrimaryCaveat]);
    +claim_support(E, case_profile, coordinator_agent, [concern_classification, fusion_confidence]);
    .send(explanation_agent, achieve, build_explanation(E, Hazard, Severity, ClaimLabel, ExposureClass, ConcernLevel, FusionConfidence, InterpretationMode, Profile, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent)).

+explanation_artifact(E, Headline, AssessmentSentence, FusionSentence, CaveatSentence, ExplanationTrace)[source(explanation_agent)] :
    integrated_case(E, Hazard, Severity, ClaimLabel, ExposureClass, ConcernLevel, FusionConfidence, InterpretationMode, Profile, SourceAgent) <-
    +final_explanation(E, Headline, AssessmentSentence, FusionSentence, CaveatSentence);
    +claim_support(E, explanation_generation, explanation_agent, [ClaimLabel, FusionConfidence, ExplanationTrace]);
    ?reference_hazard(E, ReferenceHazard);
    ?reference_severity(E, ReferenceSeverity);
    ?reference_confidence(E, ReferenceConfidence);
    !match_label(Hazard, ReferenceHazard, HazardMatch);
    !match_label(Severity, ReferenceSeverity, SeverityMatch);
    !match_label(FusionConfidence, ReferenceConfidence, ConfidenceMatch);
    .concat("-----\nEvent: ", E, Block1);
    .concat(Block1, "\nIntegrated symbolic case: hazard=", Block2);
    .concat(Block2, Hazard, Block3);
    .concat(Block3, ", severity=", Block4);
    .concat(Block4, Severity, Block5);
    .concat(Block5, ", claim=", Block6);
    .concat(Block6, ClaimLabel, Block7);
    .concat(Block7, ", exposure=", Block8);
    .concat(Block8, ExposureClass, Block9);
    .concat(Block9, ", concern=", Block10);
    .concat(Block10, ConcernLevel, Block11);
    .concat(Block11, ", fusion_confidence=", Block12);
    .concat(Block12, FusionConfidence, Block13);
    .concat(Block13, ", interpretation=", Block14);
    .concat(Block14, InterpretationMode, Block15);
    .concat(Block15, ", profile=", Block16);
    .concat(Block16, Profile, Block17);
    .concat(Block17, ", source_agent=", Block18);
    .concat(Block18, SourceAgent, Block19);
    .concat(Block19, "\nExplanation trace: ", Block20);
    .concat(Block20, ExplanationTrace, Block21);
    .concat(Block21, "\n", Block22);
    .concat(Block22, Headline, Block23);
    .concat(Block23, "\n", Block24);
    .concat(Block24, AssessmentSentence, Block25);
    .concat(Block25, "\n", Block26);
    .concat(Block26, FusionSentence, Block27);
    .concat(Block27, "\n", Block28);
    .concat(Block28, CaveatSentence, Block29);
    .concat(Block29, "\nReference alignment: hazard=", Block30);
    .concat(Block30, HazardMatch, Block31);
    .concat(Block31, ", severity=", Block32);
    .concat(Block32, SeverityMatch, Block33);
    .concat(Block33, ", confidence=", Block34);
    .concat(Block34, ConfidenceMatch, FullBlock);
    .print(FullBlock).

+!match_label(Value, Value, match) <- true.
+!match_label(Value, Reference, differs) : Value \== Reference <- true.

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
