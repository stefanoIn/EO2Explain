// Auto-generated for UI job
country_name(da, "da").
region_name(a, "a").

event(a).
name(a, "da").
country(a, da).
region(a, a).
event_type(a, flood).
timeline_confidence(a, confirmed).
late_observation_flag(a, true).
possible_underestimation(a, true).

hazard_family(flood, water_agent).
hazard_family(wildfire, forest_agent).

agent_responsible(E, Agent) :-
    event_type(E, HazardType) &
    hazard_family(HazardType, Agent).
