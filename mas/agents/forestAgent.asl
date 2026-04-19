{ include("./beliefs/events.asl") }
{ include("./beliefs/indicators.asl") }

!start.

+!start <-
    .print("FOREST AGENT started");
    .custom.trace_line("FOREST AGENT", "Started wildfire specialist.").

// The forest agent reasons in layers: raw indicators become evidence signals,
// then those signals are combined into severity, confidence, and caveat outputs.
+!assess_event(E, Requester) : fire_severity_path(E, Severity, ClaimLabel, EvidenceList, RuleLabel) <-
    ?fire_support_level(E, SupportLevel);
    ?fire_conclusion_status(Severity, ClaimLabel, ConclusionStatus);
    ?fire_confidence(E, ConfidenceLevel);
    ?fire_caveat_profile(E, ClaimLabel, PrimaryCaveat, CaveatList);
    .print("first-pass ", E, " -> support=", SupportLevel, ", severity=", Severity, ", status=", ConclusionStatus, ", confidence=", ConfidenceLevel, ", claim=", ClaimLabel, ", caveat=", PrimaryCaveat);
    .concat("First-pass assessment for ", E, Msg1);
    .concat(Msg1, ": support=", Msg2);
    .concat(Msg2, SupportLevel, Msg3);
    .concat(Msg3, ", severity=", Msg4);
    .concat(Msg4, Severity, Msg5);
    .concat(Msg5, ", status=", Msg6);
    .concat(Msg6, ConclusionStatus, Msg7);
    .concat(Msg7, ", confidence=", Msg8);
    .concat(Msg8, ConfidenceLevel, Msg9);
    .concat(Msg9, ", claim=", Msg10);
    .concat(Msg10, ClaimLabel, Msg11);
    .concat(Msg11, ".", Msg12);
    .custom.trace_line("FOREST AGENT", Msg12);
    .send(Requester, tell, hazard_assessment(E, wildfire, Severity, SupportLevel, ConclusionStatus, ConfidenceLevel, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel)).

// Second-pass clarification keeps the specialist in the loop only for caveat-heavy
// cases that the coordinator decides are not straightforward.
+!clarify_assessment(E, ClaimLabel, PrimaryCaveat, Requester) <-
    ?fire_primary_limitation(E, ClaimLabel, PrimaryCaveat, PrimaryLimitation);
    ?fire_strongest_evidence(E, ClaimLabel, StrongestEvidence);
    ?fire_alternative_claim(E, ClaimLabel, PrimaryCaveat, AlternativeClaim);
    .print("clarification ", E, " -> limitation=", PrimaryLimitation, ", strongest_evidence=", StrongestEvidence, ", alternative_claim=", AlternativeClaim);
    .concat("Clarification for ", E, Msg1);
    .concat(Msg1, ": limitation=", Msg2);
    .concat(Msg2, PrimaryLimitation, Msg3);
    .concat(Msg3, ", strongest_evidence=", Msg4);
    .concat(Msg4, StrongestEvidence, Msg5);
    .concat(Msg5, ".", Msg6);
    .custom.trace_line("FOREST AGENT", Msg6);
    .send(Requester, tell, clarification_result(E, ClaimLabel, PrimaryLimitation, StrongestEvidence, AlternativeClaim, clarification_provided)).

// Threshold rationale:
// These wildfire cutoffs are prototype symbolic thresholds, not claims of
// universal EO validity. They were selected to:
// 1. reflect plausible relative ranges for NDVI, burned-area, and dNBR
//    responses,
// 2. create distinguishable support categories on the small case-study set,
//    and
// 3. preserve interpretable rule paths that can be explained downstream.
// They should therefore be read as literature-informed heuristic cutoffs that
// were tuned for a controlled EO+MAS demonstration rather than for an
// operational fire-monitoring product.
vegetation_damage_signal(E) :-
    vegetation_loss_pct(E, VegetationLoss) &
    VegetationLoss >= 12.

strong_vegetation_damage(E) :-
    vegetation_loss_pct(E, VegetationLoss) &
    VegetationLoss >= 20.

ndvi_damage_signal(E) :-
    ndvi_drop(E, NdviDrop) &
    NdviDrop >= 0.05.

strong_ndvi_damage(E) :-
    ndvi_drop(E, NdviDrop) &
    NdviDrop >= 0.10.

burn_extent_signal(E) :-
    burned_area_pct(E, BurnedArea) &
    BurnedArea >= 3.

strong_burn_extent(E) :-
    burned_area_pct(E, BurnedArea) &
    BurnedArea >= 15.

spectral_burn_signal(E) :-
    mean_dnbr(E, MeanDNBR) &
    MeanDNBR >= 0.04.

strong_spectral_burn_signal(E) :-
    mean_dnbr(E, MeanDNBR) &
    MeanDNBR >= 0.10.

contradictory_spectral_signal(E) :-
    mean_dnbr(E, MeanDNBR) &
    MeanDNBR < 0.

// These predicates separate coherent fire evidence from mixed or weak cases.
strong_multisignal_fire_evidence(E) :-
    strong_vegetation_damage(E) &
    strong_burn_extent(E) &
    strong_spectral_burn_signal(E).

coherent_fire_evidence(E) :-
    vegetation_damage_signal(E) &
    burn_extent_signal(E).

spectral_extent_fire_evidence(E) :-
    strong_burn_extent(E) &
    strong_spectral_burn_signal(E).

mixed_fire_evidence(E) :-
    vegetation_damage_signal(E) &
    burn_extent_signal(E) &
    contradictory_spectral_signal(E).

weak_fire_evidence(E) :-
    ndvi_damage_signal(E) &
    not burn_extent_signal(E) &
    not spectral_burn_signal(E).

weak_fire_evidence(E) :-
    vegetation_damage_signal(E) &
    not ndvi_damage_signal(E) &
    not burn_extent_signal(E) &
    not spectral_burn_signal(E).

temporally_limited_observation(E) :-
    timeline_confidence(E, approximate).

temporally_limited_observation(E) :-
    timeline_confidence(E, mixed_confirmed_and_approximate).

fire_confidence_reduced(E) :-
    mixed_fire_evidence(E).

fire_confidence_reduced(E) :-
    weak_fire_evidence(E).

fire_confidence_reduced(E) :-
    temporally_limited_observation(E) &
    not strong_multisignal_fire_evidence(E) &
    not spectral_extent_fire_evidence(E).

fire_interpretation_supported(E) :-
    strong_multisignal_fire_evidence(E).

fire_interpretation_supported(E) :-
    coherent_fire_evidence(E).

fire_interpretation_supported(E) :-
    spectral_extent_fire_evidence(E).

fire_interpretation_limited(E) :-
    mixed_fire_evidence(E).

fire_interpretation_limited(E) :-
    weak_fire_evidence(E).

classified_fire_support(E) :-
    strong_multisignal_fire_evidence(E).

classified_fire_support(E) :-
    spectral_extent_fire_evidence(E).

classified_fire_support(E) :-
    coherent_fire_evidence(E) &
    not spectral_extent_fire_evidence(E).

classified_fire_support(E) :-
    mixed_fire_evidence(E).

classified_fire_support(E) :-
    weak_fire_evidence(E).

fire_support_level(E, strong) :-
    strong_multisignal_fire_evidence(E).

fire_support_level(E, moderate) :-
    spectral_extent_fire_evidence(E) &
    not strong_multisignal_fire_evidence(E) &
    not mixed_fire_evidence(E).

fire_support_level(E, moderate) :-
    coherent_fire_evidence(E) &
    not strong_multisignal_fire_evidence(E) &
    not spectral_extent_fire_evidence(E) &
    not mixed_fire_evidence(E).

fire_support_level(E, conflicting) :-
    mixed_fire_evidence(E).

fire_support_level(E, weak) :-
    weak_fire_evidence(E) &
    not mixed_fire_evidence(E).

fire_support_level(E, insufficient) :-
    not classified_fire_support(E).

// Each severity path keeps only the indicators that actually support that path.
fire_severity_path(E, severe, strong_multisignal_fire_damage, [vegetation_loss_pct, burned_area_pct, mean_dnbr], rule_severe_fire_multisignal) :-
    fire_support_level(E, strong).

fire_severity_path(E, moderate, spectral_extent_fire_damage, [burned_area_pct, mean_dnbr], rule_moderate_fire_spectral_extent) :-
    fire_support_level(E, moderate) &
    spectral_extent_fire_evidence(E).

fire_severity_path(E, moderate, coherent_fire_damage, [vegetation_loss_pct, burned_area_pct], rule_moderate_fire_vegetation_extent) :-
    fire_support_level(E, moderate) &
    coherent_fire_evidence(E) &
    not spectral_extent_fire_evidence(E).

fire_severity_path(E, mild, mixed_fire_damage, [vegetation_loss_pct, burned_area_pct], rule_mild_fire_mixed_signal) :-
    fire_support_level(E, conflicting).

fire_severity_path(E, mild, ndvi_only_fire_signal, [ndvi_drop], rule_mild_fire_ndvi_only) :-
    fire_support_level(E, weak) &
    ndvi_damage_signal(E).

fire_severity_path(E, mild, vegetation_loss_only_fire_signal, [vegetation_loss_pct], rule_mild_fire_vegetation_only) :-
    fire_support_level(E, weak) &
    vegetation_damage_signal(E) &
    not ndvi_damage_signal(E).

fire_severity_path(E, undetermined, inconclusive_fire_signal, [], rule_inconclusive_fire_signal) :-
    fire_support_level(E, insufficient).

fire_conclusion_status(undetermined, inconclusive_fire_signal, inconclusive).
fire_conclusion_status(_, _, hazard_assessed).

fire_confidence(E, high) :-
    fire_support_level(E, strong).

fire_confidence(E, medium) :-
    fire_support_level(E, moderate) &
    not fire_confidence_reduced(E).

fire_confidence(E, low) :-
    fire_support_level(E, moderate) &
    fire_confidence_reduced(E).

fire_confidence(E, low) :-
    fire_support_level(E, weak).

fire_confidence(E, low) :-
    fire_support_level(E, conflicting).

fire_confidence(E, low) :-
    fire_support_level(E, insufficient).

// Caveats explain why a valid interpretation may still need a qualified reading.

// Mixed evidence + uncertain timeline
fire_caveat_profile(E, _, burn_signal_weak, [burn_signal_weak, timeline_uncertain]) :-
    mixed_fire_evidence(E) &
    timeline_confidence(E, mixed_confirmed_and_approximate).

// Mixed evidence only
fire_caveat_profile(E, _, burn_signal_weak, [burn_signal_weak]) :-
    mixed_fire_evidence(E) &
    not timeline_confidence(E, mixed_confirmed_and_approximate).

// Late observation
fire_caveat_profile(E, _, late_observation, [late_observation, possible_underestimation]) :-
    late_observation_flag(E, true) &
    possible_underestimation(E, true) &
    not mixed_fire_evidence(E).

// Timeline uncertain
fire_caveat_profile(E, _, timeline_uncertain, [timeline_uncertain]) :-
    timeline_confidence(E, mixed_confirmed_and_approximate) &
    not mixed_fire_evidence(E) &
    not late_observation_flag(E, true).

// Coarse timeline
fire_caveat_profile(E, _, coarse_timeline, [coarse_timeline]) :-
    timeline_confidence(E, approximate) &
    not late_observation_flag(E, true).

// NDVI-only weak case
fire_caveat_profile(E, ndvi_only_fire_signal, limited_multisignal_support, [limited_multisignal_support]) :-
    weak_fire_evidence(E).

// Vegetation-loss-only weak case
fire_caveat_profile(E, vegetation_loss_only_fire_signal, limited_multisignal_support, [limited_multisignal_support]) :-
    vegetation_damage_signal(E) &
    not ndvi_damage_signal(E) &
    not burn_extent_signal(E) &
    not spectral_burn_signal(E).

fire_caveat_profile(_, _, no_major_caveat, []).

// Clarification metadata remains symbolic so the explanation layer can stay grounded
// in agent-derived labels rather than in ad-hoc free text.
fire_primary_limitation(_, _, burn_signal_weak, burn_signal_weak).
fire_primary_limitation(_, _, late_observation, late_observation).
fire_primary_limitation(_, _, timeline_uncertain, timeline_uncertain).
fire_primary_limitation(_, _, coarse_timeline, coarse_timeline).
fire_primary_limitation(_, _, limited_multisignal_support, limited_multisignal_support).
fire_primary_limitation(_, _, no_major_caveat, no_additional_limitation).

fire_strongest_evidence(_, strong_multisignal_fire_damage, vegetation_loss_pct).
fire_strongest_evidence(_, coherent_fire_damage, burned_area_pct).
fire_strongest_evidence(_, spectral_extent_fire_damage, mean_dnbr).
fire_strongest_evidence(_, mixed_fire_damage, vegetation_loss_pct).
fire_strongest_evidence(_, ndvi_only_fire_signal, ndvi_drop).
fire_strongest_evidence(_, vegetation_loss_only_fire_signal, vegetation_loss_pct).
fire_strongest_evidence(_, inconclusive_fire_signal, no_dominant_evidence).

fire_alternative_claim(_, mixed_fire_damage, burn_signal_weak, inconclusive_fire_signal).
fire_alternative_claim(_, ndvi_only_fire_signal, limited_multisignal_support, inconclusive_fire_signal).
fire_alternative_claim(_, vegetation_loss_only_fire_signal, limited_multisignal_support, inconclusive_fire_signal).
fire_alternative_claim(_, _, _, no_alternative_claim).
