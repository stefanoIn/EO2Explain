#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

import numpy as np
from rasterio.warp import Resampling, reproject

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
    "mean_ndvi_before",
    "mean_ndvi_after",
    "ndvi_drop",
    "mean_nbr_before",
    "mean_nbr_after",
    "mean_dnbr",
    "vegetation_loss_pct",
    "burned_area_pct",
    "valid_pixels",
    "burned_pixels",
    "vegetated_pixels_before",
]


BEFORE_FOLDER = "before_wildfire"
AFTER_FOLDER = "after_wildfire"
VEGETATION_THRESHOLD = 0.2
BURN_DNBR_THRESHOLD = 0.27


def resample_to_match(
    src_arr: np.ndarray,
    src_transform,
    src_crs,
    dst_shape: tuple[int, int],
    dst_transform,
    dst_crs,
) -> np.ndarray:
    destination = np.empty(dst_shape, dtype="float32")
    reproject(
        source=src_arr,
        destination=destination,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        src_nodata=np.nan,
        dst_nodata=np.nan,
        resampling=Resampling.bilinear,
    )
    return destination


def compute_wildfire_metrics(event_dir: Path) -> tuple[dict[str, float | int | str], dict[str, np.ndarray | dict]]:
    before_dir = event_dir / BEFORE_FOLDER
    after_dir = event_dir / AFTER_FOLDER

    b4_before_path = find_band_file(before_dir, "B04")
    b8_before_path = find_band_file(before_dir, "B08")
    b12_before_path = find_band_file(before_dir, "B12")
    b4_after_path = find_band_file(after_dir, "B04")
    b8_after_path = find_band_file(after_dir, "B08")
    b12_after_path = find_band_file(after_dir, "B12")

    b4_before, profile, transform, crs = read_band(b4_before_path)
    b8_before, _, _, _ = read_band(b8_before_path)
    b12_before_raw, _, b12_before_transform, b12_before_crs = read_band(b12_before_path)
    b4_after, _, _, _ = read_band(b4_after_path)
    b8_after, _, _, _ = read_band(b8_after_path)
    b12_after_raw, _, b12_after_transform, b12_after_crs = read_band(b12_after_path)

    b12_before = resample_to_match(
        b12_before_raw,
        b12_before_transform,
        b12_before_crs,
        b8_before.shape,
        transform,
        crs,
    )
    b12_after = resample_to_match(
        b12_after_raw,
        b12_after_transform,
        b12_after_crs,
        b8_after.shape,
        transform,
        crs,
    )

    ndvi_before = safe_index(b8_before - b4_before, b8_before + b4_before)
    ndvi_after = safe_index(b8_after - b4_after, b8_after + b4_after)
    nbr_before = safe_index(b8_before - b12_before, b8_before + b12_before)
    nbr_after = safe_index(b8_after - b12_after, b8_after + b12_after)
    dnbr = nbr_before - nbr_after

    valid = (
        np.isfinite(ndvi_before)
        & np.isfinite(ndvi_after)
        & np.isfinite(nbr_before)
        & np.isfinite(nbr_after)
    )
    veget_before = valid & (ndvi_before > VEGETATION_THRESHOLD)
    burned = valid & (dnbr >= BURN_DNBR_THRESHOLD)

    veget_pixels_before = int(veget_before.sum())
    burned_pixels = int(burned.sum())
    valid_pixels = int(valid.sum())

    mean_ndvi_before = float(np.nanmean(ndvi_before))
    mean_ndvi_after = float(np.nanmean(ndvi_after))
    mean_nbr_before = float(np.nanmean(nbr_before))
    mean_nbr_after = float(np.nanmean(nbr_after))
    mean_dnbr = float(np.nanmean(dnbr))

    vegetation_loss_pct = np.nan
    if veget_pixels_before > 0:
        remaining_vegetation = int((veget_before & (ndvi_after > VEGETATION_THRESHOLD)).sum())
        vegetation_loss_pct = (
            100.0 * (veget_pixels_before - remaining_vegetation) / veget_pixels_before
        )

    burned_area_pct = np.nan
    if valid_pixels > 0:
        burned_area_pct = 100.0 * burned_pixels / valid_pixels

    metrics = {
        "event": event_dir.name,
        "before_folder": summary_path(before_dir),
        "after_folder": summary_path(after_dir),
        "mean_ndvi_before": mean_ndvi_before,
        "mean_ndvi_after": mean_ndvi_after,
        "ndvi_drop": mean_ndvi_before - mean_ndvi_after,
        "mean_nbr_before": mean_nbr_before,
        "mean_nbr_after": mean_nbr_after,
        "mean_dnbr": mean_dnbr,
        "vegetation_loss_pct": vegetation_loss_pct,
        "burned_area_pct": burned_area_pct,
        "valid_pixels": valid_pixels,
        "burned_pixels": burned_pixels,
        "vegetated_pixels_before": veget_pixels_before,
    }

    arrays = {
        "ndvi_before": ndvi_before,
        "ndvi_after": ndvi_after,
        "nbr_before": nbr_before,
        "nbr_after": nbr_after,
        "dnbr": dnbr,
        "valid": valid,
        "burned": burned,
        "profile": profile,
    }
    return metrics, arrays


def process_events(root_dir: Path) -> tuple[list[dict[str, float | int | str]], dict[str, dict[str, np.ndarray | dict]]]:
    results: list[dict[str, float | int | str]] = []
    arrays_by_event: dict[str, dict[str, np.ndarray | dict]] = {}

    for event_dir in sorted(path for path in root_dir.iterdir() if path.is_dir()):
        metrics, arrays = compute_wildfire_metrics(event_dir)
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


def plot_wildfire_report_figure(arrays: dict[str, np.ndarray | dict], event_name: str):
    plt = load_pyplot()
    ndvi_before = arrays["ndvi_before"]
    ndvi_after = arrays["ndvi_after"]
    dnbr = arrays["dnbr"]
    burned = arrays["burned"]

    finite_dnbr = dnbr[np.isfinite(dnbr)]
    if finite_dnbr.size > 0:
        vmax_dnbr = np.nanpercentile(finite_dnbr, 98)
        vmax_dnbr = max(vmax_dnbr, 0.1)
    else:
        vmax_dnbr = 1.0

    fig, axes = plt.subplots(2, 2, figsize=(10, 6.0))
    axes = axes.ravel()

    im0 = axes[0].imshow(ndvi_before, cmap="RdYlGn", vmin=-1, vmax=1)
    axes[0].set_title(f"{event_name} - NDVI before")
    axes[0].axis("off")
    add_matching_colorbar(fig, axes[0], im0, "NDVI")

    im1 = axes[1].imshow(ndvi_after, cmap="RdYlGn", vmin=-1, vmax=1)
    axes[1].set_title(f"{event_name} - NDVI after")
    axes[1].axis("off")
    add_matching_colorbar(fig, axes[1], im1, "NDVI")

    im2 = axes[2].imshow(dnbr, cmap="hot", vmin=0, vmax=vmax_dnbr)
    axes[2].set_title(f"{event_name} - dNBR")
    axes[2].axis("off")
    add_matching_colorbar(fig, axes[2], im2, "dNBR")

    axes[3].imshow(burned, cmap="gray", vmin=0, vmax=1)
    axes[3].set_title(f"{event_name} - Burn mask")
    axes[3].axis("off")

    fig.suptitle(
        f"{event_name}: wildfire detection from Sentinel-2 vegetation and burn indicators",
        fontsize=14,
        y=1.02,
    )
    fig.subplots_adjust(wspace=0.20, hspace=0.08, left=0.05, right=0.98, top=0.90, bottom=0.08)
    return fig


def build_figure_path(event_name: str, figure_out: str | None, figure_dir: str | None) -> Path:
    if figure_out:
        return Path(figure_out)
    filename = f"{event_name}_wildfire_report_figure.png"
    if figure_dir:
        return Path(figure_dir) / filename
    return Path(filename)


def save_wildfire_figure(arrays: dict[str, np.ndarray | dict], event_name: str, figure_path: Path) -> None:
    plt = load_pyplot()
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure = plot_wildfire_report_figure(arrays, event_name)
    figure.savefig(figure_path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    print(f"Saved figure to: {figure_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute wildfire EO indicators from Sentinel-2 TIFF folders."
    )
    parser.add_argument(
        "--root-dir",
        default=str(PROJECT_ROOT / "data/raw/wildfires"),
        help="Directory containing one subdirectory per wildfire event.",
    )
    parser.add_argument(
        "--output-csv",
        default=str(PROJECT_ROOT / "data/processed/indicators/wildfire_eo_indicators_summary.csv"),
        help="Output CSV path for the wildfire summary table.",
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
            save_wildfire_figure(arrays, event_name, figure_path)

    if args.figure_event:
        if args.figure_event not in arrays_by_event:
            raise SystemExit(f"Unknown event for figure rendering: {args.figure_event}")
        figure_path = build_figure_path(args.figure_event, args.figure_out, args.figure_dir)
        save_wildfire_figure(arrays_by_event[args.figure_event], args.figure_event, figure_path)


if __name__ == "__main__":
    main()
