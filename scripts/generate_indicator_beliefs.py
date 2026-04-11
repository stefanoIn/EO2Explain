#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def normalize_token(value: str) -> str:
    normalized = value.strip()
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized)
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def parse_fact(pattern: str, line: str) -> tuple[str, ...] | None:
    match = re.match(pattern, line.strip())
    if match:
        return match.groups()
    return None


def load_event_catalog(events_asl: Path) -> dict[str, dict[str, str]]:
    country_names: dict[str, str] = {}
    region_names: dict[str, str] = {}
    catalog: dict[str, dict[str, str]] = {}

    for raw_line in events_asl.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue

        parsed = parse_fact(r'^country_name\(([^,]+),\s*"([^"]+)"\)\.$', line)
        if parsed:
            country_names[parsed[0]] = parsed[1]
            continue

        parsed = parse_fact(r'^region_name\(([^,]+),\s*"([^"]+)"\)\.$', line)
        if parsed:
            region_names[parsed[0]] = parsed[1]
            continue

        parsed = parse_fact(r"^event\(([^)]+)\)\.$", line)
        if parsed:
            catalog.setdefault(parsed[0], {"event_id": parsed[0]})
            continue

        parsed = parse_fact(r'^name\(([^,]+),\s*"([^"]+)"\)\.$', line)
        if parsed:
            catalog.setdefault(parsed[0], {"event_id": parsed[0]})["event_name"] = parsed[1]
            continue

        parsed = parse_fact(r"^country\(([^,]+),\s*([^)]+)\)\.$", line)
        if parsed:
            catalog.setdefault(parsed[0], {"event_id": parsed[0]})["country_id"] = parsed[1]
            continue

        parsed = parse_fact(r"^region\(([^,]+),\s*([^)]+)\)\.$", line)
        if parsed:
            catalog.setdefault(parsed[0], {"event_id": parsed[0]})["region_id"] = parsed[1]
            continue

        parsed = parse_fact(r"^event_type\(([^,]+),\s*([^)]+)\)\.$", line)
        if parsed:
            catalog.setdefault(parsed[0], {"event_id": parsed[0]})["hazard_type"] = parsed[1]

    for event in catalog.values():
        country_id = event.get("country_id", "")
        region_id = event.get("region_id", "")
        event["country_name"] = country_names.get(country_id, "")
        event["region_name"] = region_names.get(region_id, "")

    return catalog


def row_tokens(row: dict[str, str]) -> set[str]:
    tokens: set[str] = set()
    for key in ("event", "country", "population_exposure_class"):
        value = row.get(key, "")
        if value:
            tokens.add(normalize_token(value))

    for key in ("before_folder", "after_folder", "crop_path"):
        value = row.get(key, "")
        if not value:
            continue
        path = Path(value)
        for part in path.parts:
            token = normalize_token(part)
            if token and token not in {"data", "raw", "processed", "floods", "wildfires", "exposure", "cropped_to_events", "before_flooding", "after_flooding", "before_wildfire", "after_wildfire"}:
                tokens.add(token)
        if path.parent.name:
            tokens.add(normalize_token(path.parent.name))
        if len(path.parents) > 1:
            tokens.add(normalize_token(path.parents[1].name))
        stem = normalize_token(path.stem.replace("_pop_crop", ""))
        if stem:
            tokens.add(stem)

    tokens.discard("")
    return tokens


def event_tokens(event: dict[str, str]) -> set[str]:
    tokens = {
        normalize_token(event.get("event_id", "")),
        normalize_token(event.get("event_name", "")),
        normalize_token(event.get("country_id", "")),
        normalize_token(event.get("country_name", "")),
        normalize_token(event.get("region_id", "")),
        normalize_token(event.get("region_name", "")),
    }
    tokens.discard("")
    return tokens


def resolve_event_id(row: dict[str, str], catalog: dict[str, dict[str, str]], source_name: str, hazard_type: str | None = None) -> str:
    tokens = row_tokens(row)
    candidates = [
        event for event in catalog.values()
        if hazard_type is None or event.get("hazard_type") == hazard_type
    ]
    scored: list[tuple[int, str]] = []

    for event in candidates:
        etokens = event_tokens(event)
        score = 0
        for token in tokens:
            if token == normalize_token(event.get("event_id", "")):
                score += 6
            elif token == normalize_token(event.get("event_name", "")):
                score += 5
            elif token == normalize_token(event.get("region_id", "")) or token == normalize_token(event.get("region_name", "")):
                score += 4
            elif token == normalize_token(event.get("country_id", "")) or token == normalize_token(event.get("country_name", "")):
                score += 2
            elif token in etokens:
                score += 1
        if score > 0:
            scored.append((score, event["event_id"]))

    if not scored:
        raise ValueError(f"Could not resolve event mapping for row '{row.get('event', '')}' in {source_name}")

    scored.sort(reverse=True)
    top_score = scored[0][0]
    top_ids = sorted(event_id for score, event_id in scored if score == top_score)
    if len(top_ids) != 1:
        raise ValueError(
            f"Ambiguous event mapping for row '{row.get('event', '')}' in {source_name}: {', '.join(top_ids)}"
        )
    return top_ids[0]


def format_float(value: str, decimals: int) -> str:
    return f"{float(value):.{decimals}f}"


def build_flood_section(rows: list[dict[str, str]], catalog: dict[str, dict[str, str]]) -> list[str]:
    lines = [
        "// ----------------------------------------------",
        "// Flood indicators",
        "// Auto-generated from data/processed/indicators/flood_eo_indicators_summary.csv",
        "// ----------------------------------------------",
        "",
    ]
    for row in rows:
        event_id = resolve_event_id(row, catalog, "flood CSV", hazard_type="flood")
        lines.extend(
            [
                f"mean_ndwi_before({event_id}, {format_float(row['mean_ndwi_before'], 4)}).",
                f"mean_ndwi_after({event_id}, {format_float(row['mean_ndwi_after'], 4)}).",
                f"ndwi_change({event_id}, {format_float(row['ndwi_change'], 4)}).",
                f"water_increase_pct({event_id}, {format_float(row['water_increase_pct_points'], 2)}).",
                f"newly_flooded_area_pct({event_id}, {format_float(row['newly_flooded_area_pct'], 2)}).",
                "",
            ]
        )
    return lines


def build_wildfire_section(rows: list[dict[str, str]], catalog: dict[str, dict[str, str]]) -> list[str]:
    lines = [
        "// ----------------------------------------------",
        "// Wildfire indicators",
        "// Auto-generated from data/processed/indicators/wildfire_eo_indicators_summary.csv",
        "// ----------------------------------------------",
        "",
    ]
    for row in rows:
        event_id = resolve_event_id(row, catalog, "wildfire CSV", hazard_type="wildfire")
        lines.extend(
            [
                f"mean_ndvi_before({event_id}, {format_float(row['mean_ndvi_before'], 4)}).",
                f"mean_ndvi_after({event_id}, {format_float(row['mean_ndvi_after'], 4)}).",
                f"ndvi_drop({event_id}, {format_float(row['ndvi_drop'], 4)}).",
                f"mean_dnbr({event_id}, {format_float(row['mean_dnbr'], 4)}).",
                f"vegetation_loss_pct({event_id}, {format_float(row['vegetation_loss_pct'], 2)}).",
                f"burned_area_pct({event_id}, {format_float(row['burned_area_pct'], 2)}).",
                "",
            ]
        )
    return lines


def build_population_section(rows: list[dict[str, str]], catalog: dict[str, dict[str, str]]) -> list[str]:
    population_lines = [
        "// ----------------------------------------------",
        "// Population exposure indicators",
        "// Auto-generated from data/processed/exposure/population_exposure_summary.csv",
        "// Generated by scripts/generate_indicator_beliefs.py",
        "// ----------------------------------------------",
        "",
    ]

    for row in rows:
        event_id = resolve_event_id(row, catalog, "population CSV")
        population_lines.extend(
            [
                f"total_population({event_id}, {format_float(row['total_population'], 2)}).",
                f"population_area_km2({event_id}, {format_float(row['area_km2'], 4)}).",
                f"population_density_km2({event_id}, {format_float(row['population_density_km2'], 2)}).",
                f"population_exposure_class({event_id}, {row['population_exposure_class']}).",
                f"population_valid_pixels({event_id}, {int(float(row['valid_pixels']))}).",
                "",
            ]
        )

    return population_lines


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Jason .asl belief files from EO indicator CSV summaries."
    )
    parser.add_argument(
        "--flood-csv",
        default="data/processed/indicators/flood_eo_indicators_summary.csv",
        help="Flood EO summary CSV path.",
    )
    parser.add_argument(
        "--wildfire-csv",
        default="data/processed/indicators/wildfire_eo_indicators_summary.csv",
        help="Wildfire EO summary CSV path.",
    )
    parser.add_argument(
        "--population-csv",
        default="data/processed/exposure/population_exposure_summary.csv",
        help="Population exposure summary CSV path.",
    )
    parser.add_argument(
        "--events-asl",
        default="mas/beliefs/events.asl",
        help="Events belief file used as the source of truth for event metadata and automatic mapping.",
    )
    parser.add_argument(
        "--indicators-out",
        default="mas/beliefs/indicators.asl",
        help="Output path for combined indicators beliefs.",
    )
    parser.add_argument(
        "--population-out",
        default="mas/beliefs/population_exposure.asl",
        help="Output path for population exposure beliefs.",
    )
    args = parser.parse_args()

    flood_csv = resolve_project_path(args.flood_csv)
    wildfire_csv = resolve_project_path(args.wildfire_csv)
    population_csv = resolve_project_path(args.population_csv)
    events_asl = resolve_project_path(args.events_asl)
    indicators_out = resolve_project_path(args.indicators_out)
    population_out = resolve_project_path(args.population_out)

    flood_rows = read_csv_rows(flood_csv)
    wildfire_rows = read_csv_rows(wildfire_csv)
    population_rows = read_csv_rows(population_csv)
    catalog = load_event_catalog(events_asl)

    population_only_lines = build_population_section(population_rows, catalog)
    indicator_lines = build_flood_section(flood_rows, catalog) + build_wildfire_section(wildfire_rows, catalog)

    write_lines(indicators_out, indicator_lines)
    write_lines(population_out, population_only_lines)

    print(f"Wrote {indicators_out.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {population_out.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
