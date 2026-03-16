// ------------------------------------------------------
// Global country labels (useful for NLG)
// ------------------------------------------------------

country_name(germany, "Germany").
country_name(pakistan, "Pakistan").
country_name(italy, "Italy").
country_name(greece, "Greece").
country_name(turkey, "Turkey").
country_name(portugal, "Portugal").

// ------------------------------------------------------
// Global region labels (useful for NLG)
// ------------------------------------------------------

region_name(rhineland_palatinate, "Rhineland-Palatinate").
region_name(sindh_province, "Sindh Province").
region_name(emilia_romagna, "Emilia-Romagna").
region_name(eastern_macedonia_and_thrace, "Eastern Macedonia and Thrace").
region_name(mediterranean_region, "Mediterranean Region").
region_name(centro_region, "Centro Region").

// ------------------------------------------------------
// Flood events
// ------------------------------------------------------

event(ahr_valley).
name(ahr_valley, "Ahr Valley").
country(ahr_valley, germany).
region(ahr_valley, rhineland_palatinate).
event_type(ahr_valley, flood).
hazard_domain(ahr_valley, hydrological).
agent_responsible(ahr_valley, water_agent).
pair_type(ahr_valley, before_after_comparison).
before_date(ahr_valley, "2021-03-30").
after_date(ahr_valley, "2021-07-21").
year(ahr_valley, 2021).
bbox(ahr_valley, 6.950227, 50.471351, 7.18725, 50.566012).

event(sindh).
name(sindh, "Sindh").
country(sindh, pakistan).
region(sindh, sindh_province).
event_type(sindh, flood).
hazard_domain(sindh, hydrological).
agent_responsible(sindh, water_agent).
pair_type(sindh, before_after_comparison).
before_date(sindh, "2022-07-12").
after_date(sindh, "2022-09-10").
year(sindh, 2022).
bbox(sindh, 67.67564, 27.258053, 68.528303, 27.914313).

event(emilia).
name(emilia, "Emilia-Romagna").
country(emilia, italy).
region(emilia, emilia_romagna).
event_type(emilia, flood).
hazard_domain(emilia, hydrological).
agent_responsible(emilia, water_agent).
pair_type(emilia, before_after_comparison).
before_date(emilia, "2023-04-03").
after_date(emilia, "2023-05-23").
year(emilia, 2023).
bbox(emilia, 11.820598, 44.502971, 12.032391, 44.573716).

// ------------------------------------------------------
// Wildfire events
// ------------------------------------------------------

event(evros).
name(evros, "Evros").
country(evros, greece).
region(evros, eastern_macedonia_and_thrace).
event_type(evros, wildfire).
hazard_domain(evros, ecological).
agent_responsible(evros, forest_agent).
pair_type(evros, before_after_comparison).
before_date(evros, "2023-07-14").
after_date(evros, "2023-08-23").
year(evros, 2023).
bbox(evros, 25.144957, 40.781609, 26.258694, 41.221014).

event(antalya).
name(antalya, "Antalya").
country(antalya, turkey).
region(antalya, mediterranean_region).
event_type(antalya, wildfire).
hazard_domain(antalya, ecological).
agent_responsible(antalya, forest_agent).
pair_type(antalya, before_after_comparison).
before_date(antalya, "2021-06-30").
after_date(antalya, "2021-07-30").
year(antalya, 2021).
bbox(antalya, 30.938848, 36.610847, 32.116923, 37.114228).

event(serra_de_estrela).
name(serra_de_estrela, "Serra da Estrela").
country(serra_de_estrela, portugal).
region(serra_de_estrela, centro_region).
event_type(serra_de_estrela, wildfire).
hazard_domain(serra_de_estrela, ecological).
agent_responsible(serra_de_estrela, forest_agent).
pair_type(serra_de_estrela, before_after_comparison).
before_date(serra_de_estrela, "2022-08-02").
after_date(serra_de_estrela, "2022-08-22").
year(serra_de_estrela, 2022).
bbox(serra_de_estrela, -7.764595, 40.300913, -7.196839, 40.547715).