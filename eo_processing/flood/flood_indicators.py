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
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    return plt


def add_matching_colorbar(fig, ax, image, label: str) -> None:
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="4.5%", pad=0.14)
    colorbar = fig.colorbar(image, cax=cax)
    colorbar.ax.yaxis.set_ticks_position("right")
    colorbar.ax.yaxis.set_label_position("right")
    colorbar.ax.tick_params(
        axis="y",
        which="both",
        left=False,
        right=True,
        labelleft=False,
        labelright=True,
        pad=2,
    )
    colorbar.set_label(label)


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

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 3.5))
    axes = axes.ravel()

    im0 = axes[0].imshow(ndwi_before, cmap="Blues", vmin=-1, vmax=1)
    axes[0].set_title(f"{event_name} - NDWI before")
    axes[0].axis("off")
    add_matching_colorbar(fig, axes[0], im0, "NDWI")

    im1 = axes[1].imshow(ndwi_after, cmap="Blues", vmin=-1, vmax=1)
    axes[1].set_title(f"{event_name} - NDWI after")
    axes[1].axis("off")
    add_matching_colorbar(fig, axes[1], im1, "NDWI")

    im2 = axes[2].imshow(ndwi_change, cmap="RdBu", vmin=-vmax_change, vmax=vmax_change)
    axes[2].set_title(f"{event_name} - NDWI change")
    axes[2].axis("off")
    add_matching_colorbar(fig, axes[2], im2, r"$\Delta$NDWI")

    fig.suptitle(
        f"{event_name}: flood detection from Sentinel-2 NDWI",
        fontsize=14,
        y=1.04,
    )
    fig.subplots_adjust(wspace=0.20, left=0.04, right=0.99, top=0.92, bottom=0.08)
    return fig


def build_figure_path(event_name: str, figure_out: str | None, figure_dir: str | None) -> Path:
    if figure_out:
        return Path(figure_out)
    filename = f"{event_name}_flood_report_figure.png"
    if figure_dir:
        return Path(figure_dir) / filename
    return Path(filename)


def save_flood_figure(arrays: dict[str, np.ndarray | dict], event_name: str, figure_path: Path) -> None:
    plt = load_pyplot()
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure = plot_flood_report_figure(arrays, event_name)
    figure.savefig(figure_path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    print(f"Saved figure to: {figure_path}")


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
    parser.add_argument(
        "--figure-dir",
        default=None,
        help="Optional output directory used when rendering figures for multiple events.",
    )
    parser.add_argument(
        "--figure-all",
        action="store_true",
        help="Render report figures for all events in the root directory.",
    )
    args = parser.parse_args()

    root_dir = Path(args.root_dir)
    output_csv = Path(args.output_csv)

    rows, arrays_by_event = process_events(root_dir)
    write_summary_csv(rows, output_csv)
    print(f"Saved summary to: {output_csv}")

    if args.figure_all:
        for event_name, arrays in arrays_by_event.items():
            figure_path = build_figure_path(event_name, None, args.figure_dir)
            save_flood_figure(arrays, event_name, figure_path)

    if args.figure_event:
        if args.figure_event not in arrays_by_event:
            raise SystemExit(f"Unknown event for figure rendering: {args.figure_event}")
        figure_path = build_figure_path(args.figure_event, args.figure_out, args.figure_dir)
        save_flood_figure(arrays_by_event[args.figure_event], args.figure_event, figure_path)


if __name__ == "__main__":
    main()
