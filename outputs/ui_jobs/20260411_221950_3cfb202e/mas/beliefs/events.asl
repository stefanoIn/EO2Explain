// Auto-generated for UI job
country_name(ada, "ada").
region_name(ad, "ad").

event(ad).
name(ad, "ada").
country(ad, ada).
region(ad, ad).
event_type(ad, flood).
timeline_confidence(ad, confirmed).
late_observation_flag(ad, true).
possible_underestimation(ad, true).

hazard_family(flood, water_agent).
hazard_family(wildfire, forest_agent).

agent_responsible(E, Agent) :-
    event_type(E, HazardType) &
    hazard_family(HazardType, Agent).
