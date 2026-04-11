// Auto-generated for UI job
country_name(a, "a").
region_name(a, "a").

event(a).
name(a, "a").
country(a, a).
region(a, a).
event_type(a, wildfire).
timeline_confidence(a, mixed_confirmed_and_approximate).
late_observation_flag(a, true).
possible_underestimation(a, true).

hazard_family(flood, water_agent).
hazard_family(wildfire, forest_agent).

agent_responsible(E, Agent) :-
    event_type(E, HazardType) &
    hazard_family(HazardType, Agent).
