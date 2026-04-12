// Auto-generated for UI job
country_name(ad, "ad").
region_name(ad, "ad").

event(ad).
name(ad, "ad").
country(ad, ad).
region(ad, ad).
event_type(ad, flood).
timeline_confidence(ad, approximate).
late_observation_flag(ad, false).
possible_underestimation(ad, false).

hazard_family(flood, water_agent).
hazard_family(wildfire, forest_agent).

agent_responsible(E, Agent) :-
    event_type(E, HazardType) &
    hazard_family(HazardType, Agent).
