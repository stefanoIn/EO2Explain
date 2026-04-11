#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from eo_processing.common import find_band_file, read_band, safe_index


def load_pyplot():
    import matplotlib.pyplot as plt

    return plt


def summary_path(path: Path) -> str:
    return str(Path("../..") / path.relative_to(PROJECT_ROOT))


SUMMARY_FIELDS = [
    "event",
    "before_folder",
    "after_folder",
    "mean_ndwi_before",
    "mean_ndwi_after",
    "ndwi_change",
    "water_area_before_pct",
    "water_area_after_pct",
    "water_increase_pct_points",
    "newly_flooded_area_pct",
    "valid_pixels",
    "water_before_pixels",
    "water_after_pixels",
    "new_flood_pixels",
]


BEFORE_FOLDER = "before_flooding"
AFTER_FOLDER = "after_flooding"
WATER_NDWI_THRESHOLD = 0.0


def compute_flood_metrics(event_dir: Path) -> tuple[dict[str, float | int | str], dict[str, np.ndarray | dict]]:
    before_dir = event_dir / BEFORE_FOLDER
    after_dir = event_dir / AFTER_FOLDER

    b3_before_path = find_band_file(before_dir, "B03")
    b8_before_path = find_band_file(before_dir, "B08")
    b3_after_path = find_band_file(after_dir, "B03")
    b8_after_path = find_band_file(after_dir, "B08")

    b3_before, profile, _, _ = read_band(b3_before_path)
    b8_before, _, _, _ = read_band(b8_before_path)
    b3_after, _, _, _ = read_band(b3_after_path)
    b8_after, _, _, _ = read_band(b8_after_path)

    ndwi_before = safe_index(b3_before - b8_before, b3_before + b8_before)
    ndwi_after = safe_index(b3_after - b8_after, b3_after + b8_after)

    valid = np.isfinite(ndwi_before) & np.isfinite(ndwi_after)
    water_before = valid & (ndwi_before > WATER_NDWI_THRESHOLD)
    water_after = valid & (ndwi_after > WATER_NDWI_THRESHOLD)
    new_flood = valid & (~water_before) & water_after

    valid_pixels = int(valid.sum())
    water_before_pixels = int(water_before.sum())
    water_after_pixels = int(water_after.sum())
    new_flood_pixels = int(new_flood.sum())

    metrics = {
        "event": event_dir.name,
        "before_folder": summary_path(before_dir),
        "after_folder": summary_path(after_dir),
        "mean_ndwi_before": float(np.nanmean(ndwi_before)),
        "mean_ndwi_after": float(np.nanmean(ndwi_after)),
        "ndwi_change": float(np.nanmean(ndwi_after) - np.nanmean(ndwi_before)),
        "water_area_before_pct": 100.0 * water_before_pixels / valid_pixels if valid_pixels else np.nan,
        "water_area_after_pct": 100.0 * water_after_pixels / valid_pixels if valid_pixels else np.nan,
        "water_increase_pct_points": (
            100.0 * water_after_pixels / valid_pixels
            - 100.0 * water_before_pixels / valid_pixels
        ) if valid_pixels else np.nan,
        "newly_flooded_area_pct": 100.0 * new_flood_pixels / valid_pixels if valid_pixels else np.nan,
        "valid_pixels": valid_pixels,
        "water_before_pixels": water_before_pixels,
        "water_after_pixels": water_after_pixels,
        "new_flood_pixels": new_flood_pixels,
    }

    arrays = {
        "ndwi_before": ndwi_before,
        "ndwi_after": ndwi_after,
        "water_before": water_before,
        "water_after": water_after,
        "new_flood": new_flood,
        "profile": profile,
    }
    return metrics, arrays


def process_events(root_dir: Path) -> tuple[list[dict[str, float | int | str]], dict[str, dict[str, np.ndarray | dict]]]:
    results: list[dict[str, float | int | str]] = []
    arrays_by_event: dict[str, dict[str, np.ndarray | dict]] = {}

    for event_dir in sorted(path for path in root_dir.iterdir() if path.is_dir()):
        metrics, arrays = compute_flood_metrics(event_dir)
        results.append(metrics)
        arrays_by_event[event_dir.name] = arrays

    results.sort(key=lambda item: str(item["event"]))
    return results, arrays_by_event


def write_summary_csv(rows: list[dict[str, float | int | str]], output_csv: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_flood_report_figure(arrays: dict[str, np.ndarray | dict], event_name: str):
    plt = load_pyplot()
    ndwi_before = arrays["ndwi_before"]
    ndwi_after = arrays["ndwi_after"]
    water_before = arrays["water_before"]
    water_after = arrays["water_after"]
    new_flood = arrays["new_flood"]

    ndwi_change = np.where(
        np.isfinite(ndwi_before) & np.isfinite(ndwi_after),
        ndwi_after - ndwi_before,
        np.nan,
    )

    finite_change = ndwi_change[np.isfinite(ndwi_change)]
    if finite_change.size > 0:
        vmax_change = np.nanpercentile(np.abs(finite_change), 98)
        vmax_change = max(vmax_change, 0.05)
    else:
        vmax_change = 0.2

    fig, axes = plt.subplots(2, 3, figsize=(15, 9), constrained_layout=True)
    axes = axes.ravel()

    im0 = axes[0].imshow(ndwi_before, cmap="Blues", vmin=-1, vmax=1)
    axes[0].set_title(f"{event_name} - NDWI before")
    axes[0].axis("off")
    fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04).set_label("NDWI")

    im1 = axes[1].imshow(ndwi_after, cmap="Blues", vmin=-1, vmax=1)
    axes[1].set_title(f"{event_name} - NDWI after")
    axes[1].axis("off")
    fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04).set_label("NDWI")

    axes[2].imshow(new_flood, cmap="gray", vmin=0, vmax=1)
    axes[2].set_title(f"{event_name} - Newly flooded area")
    axes[2].axis("off")

    axes[3].imshow(water_before, cmap="gray", vmin=0, vmax=1)
    axes[3].set_title(f"{event_name} - Water mask before")
    axes[3].axis("off")

    axes[4].imshow(water_after, cmap="gray", vmin=0, vmax=1)
    axes[4].set_title(f"{event_name} - Water mask after")
    axes[4].axis("off")

    im5 = axes[5].imshow(ndwi_change, cmap="RdBu", vmin=-vmax_change, vmax=vmax_change)
    axes[5].set_title(f"{event_name} - NDWI change")
    axes[5].axis("off")
    fig.colorbar(im5, ax=axes[5], fraction=0.046, pad=0.04).set_label(r"$\Delta$NDWI")

    fig.suptitle(
        f"{event_name}: flood detection from Sentinel-2 NDWI and derived masks",
        fontsize=14,
        y=1.02,
    )
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute flood EO indicators from Sentinel-2 TIFF folders."
    )
    parser.add_argument(
        "--root-dir",
        default=str(PROJECT_ROOT / "data/raw/floods"),
        help="Directory containing one subdirectory per flood event.",
    )
    parser.add_argument(
        "--output-csv",
        default=str(PROJECT_ROOT / "data/processed/indicators/flood_eo_indicators_summary.csv"),
        help="Output CSV path for the flood summary table.",
    )
    parser.add_argument(
        "--figure-event",
        default=None,
        help="Optional event name to render as a report figure.",
    )
    parser.add_argument(
        "--figure-out",
        default=None,
        help="Optional output path for the rendered figure.",
    )
    args = parser.parse_args()

    root_dir = Path(args.root_dir)
    output_csv = Path(args.output_csv)

    rows, arrays_by_event = process_events(root_dir)
    write_summary_csv(rows, output_csv)
    print(f"Saved summary to: {output_csv}")

    if args.figure_event:
        if args.figure_event not in arrays_by_event:
            raise SystemExit(f"Unknown event for figure rendering: {args.figure_event}")
        plt = load_pyplot()
        figure_path = Path(args.figure_out) if args.figure_out else Path(
            f"{args.figure_event}_flood_report_figure.png"
        )
        figure = plot_flood_report_figure(arrays_by_event[args.figure_event], args.figure_event)
        figure.savefig(figure_path, dpi=300, bbox_inches="tight")
        plt.close(figure)
        print(f"Saved figure to: {figure_path}")


if __name__ == "__main__":
    main()
