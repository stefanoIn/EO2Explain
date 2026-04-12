// Auto-generated for UI job
country_name(germany, "Germany").
region_name(rhineland_palatinate, "Rhineland-Palatinate").

event(ahr_valley).
name(ahr_valley, "Ahr Valley").
country(ahr_valley, germany).
region(ahr_valley, rhineland_palatinate).
event_type(ahr_valley, flood).
timeline_confidence(ahr_valley, confirmed).
late_observation_flag(ahr_valley, true).
possible_underestimation(ahr_valley, true).

hazard_family(flood, water_agent).
hazard_family(wildfire, forest_agent).

agent_responsible(E, Agent) :-
    event_type(E, HazardType) &
    hazard_family(HazardType, Agent).
