// Auto-generated for UI job
country_name(italy, "Italy").
region_name(emilia_romagna, "Emilia-Romagna").

event(emilia_flood).
name(emilia_flood, "Emilia Flood").
country(emilia_flood, italy).
region(emilia_flood, emilia_romagna).
event_type(emilia_flood, flood).
timeline_confidence(emilia_flood, confirmed).
late_observation_flag(emilia_flood, false).
possible_underestimation(emilia_flood, false).

hazard_family(flood, water_agent).
hazard_family(wildfire, forest_agent).

agent_responsible(E, Agent) :-
    event_type(E, HazardType) &
    hazard_family(HazardType, Agent).
