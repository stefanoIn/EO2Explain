{ include("./beliefs/events.asl") }
{ include("./beliefs/indicators.asl") }

!start.

+!start <-
    .print("WATER AGENT started");
    .custom.trace_line("WATER AGENT", "Started water specialist.").

// The water agent treats flood reasoning as a progression from indicator signals
// to coherent flood evidence, then to severity, confidence, and caveats.
+!assess_event(E, Requester) : flood_severity_path(E, Severity, ClaimLabel, EvidenceList, RuleLabel) <-
    ?flood_support_level(E, SupportLevel);
    ?flood_conclusion_status(Severity, ClaimLabel, ConclusionStatus);
    ?flood_confidence(E, ConfidenceLevel);
    ?flood_caveat_profile(E, ClaimLabel, PrimaryCaveat, CaveatList);
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
    .custom.trace_line("WATER AGENT", Msg12);
    .send(Requester, tell, hazard_assessment(E, flood, Severity, SupportLevel, ConclusionStatus, ConfidenceLevel, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel)).

// Second-pass clarification is only triggered by the coordinator for uncertain
// or caveat-heavy cases.
+!clarify_assessment(E, ClaimLabel, PrimaryCaveat, Requester) <-
    ?flood_primary_limitation(E, ClaimLabel, PrimaryCaveat, PrimaryLimitation);
    ?flood_strongest_evidence(E, ClaimLabel, StrongestEvidence);
    ?flood_alternative_claim(E, ClaimLabel, PrimaryCaveat, AlternativeClaim);
    .print("clarification ", E, " -> limitation=", PrimaryLimitation, ", strongest_evidence=", StrongestEvidence, ", alternative_claim=", AlternativeClaim);
    .concat("Clarification for ", E, Msg1);
    .concat(Msg1, ": limitation=", Msg2);
    .concat(Msg2, PrimaryLimitation, Msg3);
    .concat(Msg3, ", strongest_evidence=", Msg4);
    .concat(Msg4, StrongestEvidence, Msg5);
    .concat(Msg5, ".", Msg6);
    .custom.trace_line("WATER AGENT", Msg6);
    .send(Requester, tell, clarification_result(E, ClaimLabel, PrimaryLimitation, StrongestEvidence, AlternativeClaim, clarification_provided)).

// Threshold rationale:
// These flood cutoffs are prototype decision thresholds, not universal EO
// standards. They were chosen to be:
// 1. consistent with common EO intuition about weak vs. stronger NDWI/water
//    responses,
// 2. separable on the small case-study set used in this project, and
// 3. interpretable enough to support symbolic categories such as strong,
//    moderate, weak, conflicting, and inconclusive evidence.
// In other words, they are literature-informed heuristic cutoffs that were
// tuned for controlled demonstration and explanation quality rather than for
// operational deployment.
water_expansion_signal(E) :-
    water_increase_pct(E, WaterIncrease) &
    WaterIncrease >= 8.

strong_water_expansion(E) :-
    water_increase_pct(E, WaterIncrease) &
    WaterIncrease >= 20.

flood_extent_signal(E) :-
    newly_flooded_area_pct(E, NewlyFlooded) &
    NewlyFlooded >= 8.

strong_flood_extent(E) :-
    newly_flooded_area_pct(E, NewlyFlooded) &
    NewlyFlooded >= 20.

ndwi_shift_signal(E) :-
    ndwi_change(E, NdwiChange) &
    NdwiChange >= 0.08.

strong_ndwi_shift(E) :-
    ndwi_change(E, NdwiChange) &
    NdwiChange >= 0.18.

negative_ndwi_shift(E) :-
    ndwi_change(E, NdwiChange) &
    NdwiChange < 0.

weak_surface_water_trace(E) :-
    water_increase_pct(E, WaterIncrease) &
    WaterIncrease < 5 &
    newly_flooded_area_pct(E, NewlyFlooded) &
    NewlyFlooded < 5.

// Coastal baseline thresholds are intentionally looser than the main flood
// thresholds because they are only used to detect coastal false positives.
// They were introduced after observing that some coastal wildfire scenes can
// produce small NDWI changes without a real flood footprint.
// [MODIFIED] Coastal baseline filtering is restricted to NDWI-only noise.
coastal_area(E) :-
    water_area_before_pct(E, BeforeWaterArea) &
    BeforeWaterArea >= 3.

no_flood_expansion(E) :-
    newly_flooded_area_pct(E, NewlyFlooded) &
    NewlyFlooded < 2.

coastal_ndwi_shift(E) :-
    ndwi_change(E, NdwiChange) &
    NdwiChange >= 0.03.

coastal_ndwi_without_expansion(E) :-
    coastal_ndwi_shift(E) &
    not water_expansion_signal(E) &
    not flood_extent_signal(E) &
    not residual_flood_evidence(E) &
    coastal_area(E) &
    no_flood_expansion(E).

// Residual cases are kept separate from coherent flood detections because
// late acquisitions can hide peak flood extent.
strong_multisignal_flood_evidence(E) :-
    strong_water_expansion(E) &
    strong_flood_extent(E) &
    strong_ndwi_shift(E).

coherent_flood_evidence(E) :-
    water_expansion_signal(E) &
    flood_extent_signal(E) &
    ndwi_shift_signal(E).

extent_supported_flood_evidence(E) :-
    water_expansion_signal(E) &
    flood_extent_signal(E) &
    not strong_multisignal_flood_evidence(E).

residual_flood_evidence(E) :-
    weak_surface_water_trace(E) &
    late_observation_flag(E, true) &
    possible_underestimation(E, true).

weak_flood_evidence(E) :-
    ndwi_shift_signal(E) &
    not water_expansion_signal(E) &
    not flood_extent_signal(E) &
    not coastal_ndwi_without_expansion(E).

conflicting_flood_evidence(E) :-
    water_expansion_signal(E) &
    flood_extent_signal(E) &
    negative_ndwi_shift(E).

flood_confidence_reduced(E) :-
    residual_flood_evidence(E).

flood_confidence_reduced(E) :-
    weak_flood_evidence(E).

flood_interpretation_supported(E) :-
    strong_multisignal_flood_evidence(E).

flood_interpretation_supported(E) :-
    coherent_flood_evidence(E).

flood_interpretation_supported(E) :-
    extent_supported_flood_evidence(E).

flood_interpretation_limited(E) :-
    residual_flood_evidence(E).

flood_interpretation_limited(E) :-
    weak_flood_evidence(E).

flood_interpretation_limited(E) :-
    conflicting_flood_evidence(E).

classified_flood_support(E) :-
    strong_multisignal_flood_evidence(E).

classified_flood_support(E) :-
    coherent_flood_evidence(E).

classified_flood_support(E) :-
    extent_supported_flood_evidence(E).

classified_flood_support(E) :-
    residual_flood_evidence(E).

classified_flood_support(E) :-
    weak_flood_evidence(E).

classified_flood_support(E) :-
    conflicting_flood_evidence(E).

flood_support_level(E, strong) :-
    strong_multisignal_flood_evidence(E).

flood_support_level(E, moderate) :-
    coherent_flood_evidence(E) &
    not strong_multisignal_flood_evidence(E) &
    not conflicting_flood_evidence(E).

flood_support_level(E, moderate) :-
    extent_supported_flood_evidence(E) &
    not coherent_flood_evidence(E) &
    not strong_multisignal_flood_evidence(E) &
    not conflicting_flood_evidence(E).

flood_support_level(E, weak) :-
    residual_flood_evidence(E).

flood_support_level(E, weak) :-
    weak_flood_evidence(E).

flood_support_level(E, conflicting) :-
    conflicting_flood_evidence(E).

flood_support_level(E, insufficient) :-
    not classified_flood_support(E).

// The evidence list in each path is intentionally specific to that reasoning route.
flood_severity_path(E, severe, strong_multisignal_flooding, [water_increase_pct, newly_flooded_area_pct, ndwi_change], rule_severe_flood_multisignal) :-
    flood_support_level(E, strong).

flood_severity_path(E, moderate, coherent_flooding, [water_increase_pct, newly_flooded_area_pct, ndwi_change], rule_moderate_flood_coherent) :-
    flood_support_level(E, moderate) &
    coherent_flood_evidence(E).

flood_severity_path(E, moderate, extent_supported_flooding, [water_increase_pct, newly_flooded_area_pct], rule_moderate_flood_extent_supported) :-
    flood_support_level(E, moderate) &
    extent_supported_flood_evidence(E) &
    not coherent_flood_evidence(E).

flood_severity_path(E, mild, residual_flood_signal, [water_increase_pct, newly_flooded_area_pct], rule_residual_flood_late_observation) :-
    flood_support_level(E, weak) &
    residual_flood_evidence(E).

flood_severity_path(E, mild, limited_water_shift_signal, [ndwi_change], rule_mild_flood_ndwi_only) :-
    flood_support_level(E, weak) &
    weak_flood_evidence(E).

flood_severity_path(E, mild, mixed_flood_signal, [water_increase_pct, newly_flooded_area_pct], rule_mild_flood_conflicting_signal) :-
    flood_support_level(E, conflicting).

flood_severity_path(E, undetermined, inconclusive_water_signal, [ndwi_change, water_area_before_pct, newly_flooded_area_pct], rule_inconclusive_flood_coastal_baseline) :-
    coastal_ndwi_without_expansion(E).

flood_severity_path(E, undetermined, inconclusive_water_signal, [], rule_inconclusive_flood_signal) :-
    flood_support_level(E, insufficient).

flood_conclusion_status(undetermined, inconclusive_water_signal, inconclusive).
flood_conclusion_status(_, _, hazard_assessed).

flood_confidence(E, high) :-
    flood_support_level(E, strong).

flood_confidence(E, medium) :-
    flood_support_level(E, moderate) &
    not flood_confidence_reduced(E).

flood_confidence(E, low) :-
    flood_support_level(E, moderate) &
    flood_confidence_reduced(E).

flood_confidence(E, low) :-
    flood_support_level(E, weak) &
    not residual_flood_evidence(E).

flood_confidence(E, medium) :-
    flood_support_level(E, weak) &
    residual_flood_evidence(E).

flood_confidence(E, low) :-
    flood_support_level(E, conflicting).

flood_confidence(E, low) :-
    flood_support_level(E, insufficient).

// Caveats make it explicit when a flood reading depends on residual traces
// or on a weak spectral shift rather than a full coherent signature.
flood_caveat_profile(E, residual_flood_signal, residual_observation_window, [late_observation, possible_underestimation, weak_water_signal]) :-
    residual_flood_evidence(E).

flood_caveat_profile(E, _, late_observation, [late_observation, possible_underestimation]) :-
    late_observation_flag(E, true) &
    possible_underestimation(E, true) &
    not residual_flood_evidence(E).

flood_caveat_profile(E, _, timeline_uncertain, [timeline_uncertain]) :-
    timeline_confidence(E, mixed_confirmed_and_approximate) &
    not late_observation_flag(E, true).

flood_caveat_profile(E, limited_water_shift_signal, weak_water_signal, [weak_water_signal]) :-
    weak_flood_evidence(E).

flood_caveat_profile(E, mixed_flood_signal, weak_water_signal, [weak_water_signal]) :-
    conflicting_flood_evidence(E).

flood_caveat_profile(E, inconclusive_water_signal, coastal_baseline_water, [coastal_baseline_water, no_flood_expansion]) :-
    coastal_ndwi_without_expansion(E).

// [MODIFIED] Generic insufficient flood cases now carry an explicit limitation.
flood_caveat_profile(E, inconclusive_water_signal, insufficient_flood_pattern, [insufficient_flood_pattern]) :-
    flood_support_level(E, insufficient) &
    not coastal_ndwi_without_expansion(E).

flood_caveat_profile(_, _, no_major_caveat, []).

// Clarification metadata keeps the second pass symbolic and reusable.
flood_primary_limitation(_, _, coastal_baseline_water, coastal_baseline_water).
flood_primary_limitation(_, _, insufficient_flood_pattern, insufficient_flood_pattern).
flood_primary_limitation(_, _, residual_observation_window, residual_observation_window).
flood_primary_limitation(_, _, late_observation, late_observation).
flood_primary_limitation(_, _, timeline_uncertain, timeline_uncertain).
flood_primary_limitation(_, _, weak_water_signal, weak_water_signal).
flood_primary_limitation(_, _, no_major_caveat, no_additional_limitation).

flood_strongest_evidence(_, strong_multisignal_flooding, newly_flooded_area_pct).
flood_strongest_evidence(_, coherent_flooding, newly_flooded_area_pct).
flood_strongest_evidence(_, extent_supported_flooding, newly_flooded_area_pct).
flood_strongest_evidence(_, residual_flood_signal, newly_flooded_area_pct).
flood_strongest_evidence(_, limited_water_shift_signal, ndwi_change).
flood_strongest_evidence(_, mixed_flood_signal, newly_flooded_area_pct).
flood_strongest_evidence(_, inconclusive_water_signal, no_dominant_evidence).

flood_alternative_claim(_, residual_flood_signal, residual_observation_window, inconclusive_water_signal).
flood_alternative_claim(_, limited_water_shift_signal, weak_water_signal, inconclusive_water_signal).
flood_alternative_claim(_, mixed_flood_signal, weak_water_signal, inconclusive_water_signal).
flood_alternative_claim(_, _, _, no_alternative_claim).
