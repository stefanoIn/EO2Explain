#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import re
import sys

import numpy as np
import rasterio
from pyproj import Geod
from shapely.geometry import box


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVENTS_PATH = PROJECT_ROOT / "mas/beliefs/events.asl"
POP_DIR = PROJECT_ROOT / "data/processed/exposure"
CROPS_DIR = POP_DIR / "cropped_to_events"
DEFAULT_OUT_CSV = POP_DIR / "population_exposure_summary.csv"
DEFAULT_OUT_ASL = PROJECT_ROOT / "mas/beliefs/population_exposure.asl"

CSV_FIELDS = [
    "event",
    "country",
    "population_raster",
    "total_population",
    "area_km2",
    "population_density_km2",
    "valid_pixels",
    "crop_path",
    "population_exposure_class",
]


def parse_fact(pattern: str, line: str) -> tuple[str, ...] | None:
    match = re.match(pattern, line.strip())
    if match:
        return match.groups()
    return None


def load_event_metadata(events_path: Path) -> list[dict[str, object]]:
    country_map: dict[str, str] = {}
    bbox_map: dict[str, tuple[float, float, float, float]] = {}
    events: list[str] = []

    for raw_line in events_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue

        parsed = parse_fact(r"^event\(([^)]+)\)\.$", line)
        if parsed:
            events.append(parsed[0])
            continue

        parsed = parse_fact(r"^country\(([^,]+),\s*([^)]+)\)\.$", line)
        if parsed:
            country_map[parsed[0]] = parsed[1]
            continue

        parsed = parse_fact(
            r"^bbox\(([^,]+),\s*([\-0-9.]+),\s*([\-0-9.]+),\s*([\-0-9.]+),\s*([\-0-9.]+)\)\.$",
            line,
        )
        if parsed:
            bbox_map[parsed[0]] = tuple(float(value) for value in parsed[1:])

    metadata: list[dict[str, object]] = []
    for event_id in sorted(set(events)):
        if event_id in country_map and event_id in bbox_map:
            metadata.append(
                {
                    "event": event_id,
                    "country": country_map[event_id],
                    "bbox": bbox_map[event_id],
                }
            )
    return metadata


def load_crop_rasters(crops_dir: Path) -> dict[str, Path]:
    raster_by_event: dict[str, Path] = {}
    for tif_path in sorted(crops_dir.glob("*_pop_crop.tif")):
        event_id = tif_path.name.replace("_pop_crop.tif", "")
        raster_by_event[event_id] = tif_path
    return raster_by_event


def exposure_class(density: float) -> str:
    if np.isnan(density):
        return "unknown"
    if density < 100:
        return "low"
    if density < 500:
        return "medium"
    return "high"


def build_population_rows(
    event_metadata: list[dict[str, object]],
    raster_by_event: dict[str, Path],
) -> list[dict[str, object]]:
    geod = Geod(ellps="WGS84")
    rows: list[dict[str, object]] = []

    for record in event_metadata:
        event_id = str(record["event"])
        country = str(record["country"])
        minx, miny, maxx, maxy = record["bbox"]  # type: ignore[misc]

        crop_path = raster_by_event.get(event_id)
        if crop_path is None:
            continue

        geom_wgs84 = box(minx, miny, maxx, maxy)
        with rasterio.open(crop_path) as src:
            array = src.read(1).astype(float)
            if src.nodata is not None:
                array[array == src.nodata] = np.nan
            total_population = float(np.nansum(array))
            valid_pixels = int(np.sum(~np.isnan(array)))

        area_m2, _ = geod.geometry_area_perimeter(geom_wgs84)
        area_km2 = abs(area_m2) / 1e6
        density = total_population / area_km2 if area_km2 > 0 else np.nan

        rows.append(
            {
                "event": event_id,
                "country": country,
                "population_raster": crop_path.name,
                "total_population": round(total_population, 2),
                "area_km2": round(area_km2, 4),
                "population_density_km2": round(float(density), 2),
                "valid_pixels": valid_pixels,
                "crop_path": str(crop_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "population_exposure_class": exposure_class(float(density)),
            }
        )

    rows.sort(key=lambda row: str(row["event"]))
    return rows


def write_summary_csv(rows: list[dict[str, object]], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_population_asl(rows: list[dict[str, object]], output_asl: Path) -> None:
    lines = [
        "// ----------------------------------------------",
        "// Population exposure indicators",
        "// Auto-generated from data/processed/exposure/population_exposure_summary.csv",
        "// Generated by eo_processing/population/population_exposure.py",
        "// ----------------------------------------------",
        "",
    ]

    for row in rows:
        event_id = str(row["event"])
        lines.append(f"total_population({event_id}, {float(row['total_population']):.2f}).")
        lines.append(f"population_area_km2({event_id}, {float(row['area_km2']):.4f}).")
        lines.append(
            f"population_density_km2({event_id}, {float(row['population_density_km2']):.2f})."
        )
        lines.append(
            f"population_exposure_class({event_id}, {row['population_exposure_class']})."
        )
        lines.append(f"population_valid_pixels({event_id}, {int(row['valid_pixels'])}).")
        lines.append("")

    output_asl.parent.mkdir(parents=True, exist_ok=True)
    output_asl.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute population exposure metrics from event bbox metadata and cropped population rasters."
    )
    parser.add_argument(
        "--events-asl",
        default=str(EVENTS_PATH),
        help="Path to the Jason events.asl file containing bbox and country metadata.",
    )
    parser.add_argument(
        "--crops-dir",
        default=str(CROPS_DIR),
        help="Directory containing event-specific cropped population TIFFs.",
    )
    parser.add_argument(
        "--output-csv",
        default=str(DEFAULT_OUT_CSV),
        help="Output CSV path for the population exposure summary.",
    )
    parser.add_argument(
        "--output-asl",
        default=str(DEFAULT_OUT_ASL),
        help="Output ASL path for the population exposure beliefs.",
    )
    args = parser.parse_args()

    event_metadata = load_event_metadata(Path(args.events_asl))
    raster_by_event = load_crop_rasters(Path(args.crops_dir))
    rows = build_population_rows(event_metadata, raster_by_event)
    write_summary_csv(rows, Path(args.output_csv))
    write_population_asl(rows, Path(args.output_asl))

    print(f"Saved summary to: {args.output_csv}")
    print(f"Saved ASL to: {args.output_asl}")


if __name__ == "__main__":
    main()
