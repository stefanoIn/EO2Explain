// Auto-generated for UI job
country_name(qq, "qq").
region_name(qq, "qq").

event(q).
name(q, "qq").
country(q, qq).
region(q, qq).
event_type(q, flood).
timeline_confidence(q, confirmed).
late_observation_flag(q, true).
possible_underestimation(q, true).

hazard_family(flood, water_agent).
hazard_family(wildfire, forest_agent).

agent_responsible(E, Agent) :-
    event_type(E, HazardType) &
    hazard_family(HazardType, Agent).
