{ include("mas/beliefs/events.asl") }
{ include("mas/beliefs/indicators.asl") }

!start.

+!start <-
    .print("started").

// The water agent treats flood reasoning as a progression from indicator signals
// to coherent flood evidence, then to severity, confidence, and caveats.
+!assess_event(E, Requester) : flood_severity_path(E, Severity, ClaimLabel, EvidenceList, RuleLabel) <-
    ?flood_confidence(E, ConfidenceLevel);
    ?flood_caveat_profile(E, ClaimLabel, PrimaryCaveat, CaveatList);
    .print("first-pass ", E, " -> severity=", Severity, ", confidence=", ConfidenceLevel, ", claim=", ClaimLabel, ", caveat=", PrimaryCaveat);
    .send(Requester, tell, hazard_assessment(E, flood, Severity, ConfidenceLevel, ClaimLabel, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel)).

// Second-pass clarification is only triggered by the coordinator for uncertain
// or caveat-heavy cases.
+!clarify_assessment(E, ClaimLabel, PrimaryCaveat, Requester) <-
    ?flood_primary_limitation(E, ClaimLabel, PrimaryCaveat, PrimaryLimitation);
    ?flood_strongest_evidence(E, ClaimLabel, StrongestEvidence);
    ?flood_alternative_claim(E, ClaimLabel, PrimaryCaveat, AlternativeClaim);
    .print("clarification ", E, " -> limitation=", PrimaryLimitation, ", strongest_evidence=", StrongestEvidence, ", alternative_claim=", AlternativeClaim);
    .send(Requester, tell, clarification_result(E, ClaimLabel, PrimaryLimitation, StrongestEvidence, AlternativeClaim, clarification_provided)).

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
    not flood_extent_signal(E).

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

// The evidence list in each path is intentionally specific to that reasoning route.
flood_severity_path(E, severe, strong_multisignal_flooding, [water_increase_pct, newly_flooded_area_pct, ndwi_change], rule_severe_flood_multisignal) :-
    strong_multisignal_flood_evidence(E).

flood_severity_path(E, moderate, coherent_flooding, [water_increase_pct, newly_flooded_area_pct, ndwi_change], rule_moderate_flood_coherent) :-
    coherent_flood_evidence(E) &
    not strong_multisignal_flood_evidence(E).

flood_severity_path(E, moderate, extent_supported_flooding, [water_increase_pct, newly_flooded_area_pct], rule_moderate_flood_extent_supported) :-
    extent_supported_flood_evidence(E) &
    not coherent_flood_evidence(E) &
    not strong_multisignal_flood_evidence(E).

flood_severity_path(E, mild, residual_flood_signal, [water_increase_pct, newly_flooded_area_pct], rule_residual_flood_late_observation) :-
    residual_flood_evidence(E).

flood_severity_path(E, mild, limited_water_shift_signal, [ndwi_change], rule_mild_flood_ndwi_only) :-
    weak_flood_evidence(E).

flood_severity_path(E, mild, inconclusive_water_signal, [], rule_inconclusive_flood_signal) :-
    not flood_interpretation_supported(E) &
    not flood_interpretation_limited(E) &
    not ndwi_shift_signal(E).

flood_confidence(E, high) :-
    strong_multisignal_flood_evidence(E).

flood_confidence(E, high) :-
    coherent_flood_evidence(E) &
    not flood_confidence_reduced(E).

flood_confidence(E, medium) :-
    extent_supported_flood_evidence(E).

flood_confidence(E, medium) :-
    residual_flood_evidence(E).

flood_confidence(E, low) :-
    weak_flood_evidence(E).

flood_confidence(E, low) :-
    not flood_interpretation_supported(E) &
    not residual_flood_evidence(E).

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

flood_caveat_profile(_, _, no_major_caveat, []).

// Clarification metadata keeps the second pass symbolic and reusable.
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
flood_strongest_evidence(_, inconclusive_water_signal, no_dominant_evidence).

flood_alternative_claim(_, residual_flood_signal, residual_observation_window, inconclusive_water_signal).
flood_alternative_claim(_, limited_water_shift_signal, weak_water_signal, inconclusive_water_signal).
flood_alternative_claim(_, _, _, no_alternative_claim).
