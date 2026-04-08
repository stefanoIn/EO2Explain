{ include("beliefs/events.asl") }

// The explanation agent stays grounded in symbolic outputs from the other agents;
// it does not reason from raw EO indicators directly.
+!build_explanation(E, Hazard, Severity, ClaimLabel, ExposureClass, ConcernLevel, FusionConfidence, InterpretationMode, Profile, PrimaryCaveat, EvidenceList, CaveatList, RuleLabel, SourceAgent, ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim) <-
    ?name(E, EventName);
    ?country(E, CountryId);
    ?country_name(CountryId, CountryName);
    ?region(E, RegionId);
    ?region_name(RegionId, RegionName);
    ?hazard_phrase(Hazard, HazardPhrase);
    ?severity_phrase(Severity, SeverityPhrase);
    ?confidence_phrase(FusionConfidence, ConfidencePhrase);
    ?concern_phrase(ConcernLevel, ConcernPhrase);
    ?interpretation_phrase(InterpretationMode, InterpretationPhrase);
    ?exposure_phrase(ExposureClass, ExposurePhrase);
    ?claim_phrase(ClaimLabel, ClaimSentence);
    ?caveat_phrase(PrimaryCaveat, CaveatPhrase);
    ?profile_phrase(Profile, ProfilePhrase);
    !compose_clarification_sentence(ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim, ClarificationSentence);
    .concat(EventName, " in ", HeadlinePart1);
    .concat(HeadlinePart1, RegionName, HeadlinePart2);
    .concat(HeadlinePart2, ", ", HeadlinePart3);
    .concat(HeadlinePart3, CountryName, HeadlinePart4);
    .concat(HeadlinePart4, " is interpreted as a ", HeadlinePart5);
    .concat(HeadlinePart5, SeverityPhrase, HeadlinePart6);
    .concat(HeadlinePart6, " ", HeadlinePart7);
    .concat(HeadlinePart7, HazardPhrase, HeadlinePart8);
    .concat(HeadlinePart8, " case with ", HeadlinePart9);
    .concat(HeadlinePart9, ConfidencePhrase, Headline);
    .concat(ClaimSentence, " The symbolic interpretation remains ", AssessmentPart1);
    .concat(AssessmentPart1, InterpretationPhrase, AssessmentSentence);
    .concat("The coordinator fuses this hazard assessment with ", ExposurePhrase, FusionPart1);
    .concat(FusionPart1, " exposure, yielding ", FusionPart2);
    .concat(FusionPart2, ConcernPhrase, FusionPart3);
    .concat(FusionPart3, " and the profile ", FusionPart4);
    .concat(FusionPart4, ProfilePhrase, FusionSentence);
    .concat("Caveat-aware reading: ", CaveatPhrase, CaveatPart1);
    .concat(CaveatPart1, " Trace anchored in ", CaveatPart2);
    .concat(CaveatPart2, EvidenceList, CaveatPart3);
    .concat(CaveatPart3, " with caveats ", CaveatPart4);
    .concat(CaveatPart4, CaveatList, CaveatSentence);
    // The trace object is kept separate so the coordinator can print or reuse it
    // without having to recover support information from the final prose.
    .send(coordinator_agent, tell, explanation_artifact(E, Headline, AssessmentSentence, FusionSentence, CaveatSentence, ClarificationSentence, explanation_trace(SourceAgent, RuleLabel, ClaimLabel, EvidenceList, CaveatList, clarification_trace(ClarificationStatus, PrimaryLimitation, StrongestEvidence, AlternativeClaim)))).

hazard_phrase(flood, "flood").
hazard_phrase(wildfire, "wildfire").

severity_phrase(severe, "severe").
severity_phrase(moderate, "moderate").
severity_phrase(mild, "mild").

confidence_phrase(high, "high confidence").
confidence_phrase(medium, "moderate confidence").
confidence_phrase(low, "low confidence").

exposure_phrase(high, "high").
exposure_phrase(medium, "medium").
exposure_phrase(low, "low").

concern_phrase(critical, "critical concern").
concern_phrase(high, "high concern").
concern_phrase(elevated, "elevated concern").
concern_phrase(moderate, "moderate concern").
concern_phrase(guarded, "a guarded monitoring case").
concern_phrase(watch, "a watch-level case").

interpretation_phrase(robust, "robust").
interpretation_phrase(qualified, "qualified by caveats").
interpretation_phrase(cautious, "cautious").
interpretation_phrase(tentative, "tentative").

profile_phrase(critical_concern_case, "critical_concern_case").
profile_phrase(high_priority_event, "high_priority_event").
profile_phrase(confidence_limited_priority_event, "confidence_limited_priority_event").
profile_phrase(elevated_priority_event, "elevated_priority_event").
profile_phrase(cautious_monitoring_case, "cautious_monitoring_case").
profile_phrase(monitoring_case, "monitoring_case").
profile_phrase(guarded_monitoring_case, "guarded_monitoring_case").
profile_phrase(watch_case, "watch_case").

claim_phrase(strong_multisignal_fire_damage, "The wildfire signal is strong across vegetation loss, burned area, and dNBR.").
claim_phrase(coherent_fire_damage, "The wildfire interpretation is supported by coherent vegetation-loss and burned-area evidence.").
claim_phrase(spectral_extent_fire_damage, "The wildfire interpretation is supported by a strong burn-extent signal reinforced by dNBR.").
claim_phrase(mixed_fire_damage, "Wildfire damage is still supported, but the spectral signal is mixed relative to vegetation and burned-area evidence.").
claim_phrase(ndvi_only_fire_signal, "The wildfire interpretation relies on an NDVI-only vegetation-change signal rather than a broader burn signature.").
claim_phrase(vegetation_loss_only_fire_signal, "The wildfire interpretation is supported only by vegetation-loss evidence, without broader burn corroboration.").
claim_phrase(inconclusive_fire_signal, "The available wildfire evidence is inconclusive and should be interpreted conservatively.").

claim_phrase(strong_multisignal_flooding, "The flood signal is strong across water expansion, flood extent, and NDWI change.").
claim_phrase(coherent_flooding, "The flood interpretation is supported by coherent changes in water extent and NDWI.").
claim_phrase(extent_supported_flooding, "The flood interpretation is supported mainly by expanded flood extent rather than by all available indicators.").
claim_phrase(residual_flood_signal, "Only a residual flood signal remains visible, and it is interpreted in light of the observation timing.").
claim_phrase(limited_water_shift_signal, "The flood interpretation relies on a limited NDWI shift rather than a broad coherent flood signature.").
claim_phrase(inconclusive_water_signal, "The available flood evidence is inconclusive and should be treated cautiously.").

caveat_phrase(no_major_caveat, "no major caveat is active.").
caveat_phrase(late_observation, "confidence is qualified because the post-event image is temporally late.").
caveat_phrase(possible_underestimation, "the available image may underestimate peak hazard extent.").
caveat_phrase(timeline_uncertain, "the event timing mixes confirmed and approximate temporal information.").
caveat_phrase(coarse_timeline, "the event timing is only approximately constrained.").
caveat_phrase(burn_signal_weak, "the wildfire interpretation is limited by a weak or contradictory burn signal.").
caveat_phrase(weak_water_signal, "the flood interpretation is limited by a weak water signal.").
caveat_phrase(limited_multisignal_support, "the interpretation is supported by only a limited set of hazard indicators.").
caveat_phrase(residual_observation_window, "the observed flood footprint is likely residual because the image was acquired late and may underestimate peak conditions.").

// Clarification text is composed as a goal so the explanation remains grounded in
// symbolic clarification outputs from the hazard specialist.
+!compose_clarification_sentence(no_clarification, _, _, _, Sentence) <-
    .concat("No second-pass clarification was required because the first-pass specialist assessment was treated as sufficient.", "", Sentence).

+!compose_clarification_sentence(clarification_provided, PrimaryLimitation, StrongestEvidence, no_alternative_claim, Sentence) <-
    .concat("A second-pass clarification was requested. The specialist identified ", PrimaryLimitation, Part1);
    .concat(Part1, " as the main limitation and ", Part2);
    .concat(Part2, StrongestEvidence, Part3);
    .concat(Part3, " as the strongest retained evidence.", Sentence).

+!compose_clarification_sentence(clarification_provided, PrimaryLimitation, StrongestEvidence, AlternativeClaim, Sentence) : AlternativeClaim \== no_alternative_claim <-
    .concat("A second-pass clarification was requested. The specialist identified ", PrimaryLimitation, Part1);
    .concat(Part1, " as the main limitation and ", Part2);
    .concat(Part2, StrongestEvidence, Part3);
    .concat(Part3, " as the strongest retained evidence. The closest alternative claim was ", Part4);
    .concat(Part4, AlternativeClaim, Part5);
    .concat(Part5, ".", Sentence).
