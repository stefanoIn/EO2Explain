from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import rasterio

"""
This module provides common utilities for reading and 
processing EO data, such as finding band files and reading
them into numpy arrays.
"""


def find_band_file(folder: Path, band: str) -> Path:
    candidates = sorted(folder.glob("*.tif")) + sorted(folder.glob("*.tiff"))
    for candidate in candidates:
        if re.search(
            fr"[_-]{band}([_-]|\b)", candidate.name, flags=re.IGNORECASE
        ) or band.lower() in candidate.name.lower():
            return candidate
    raise FileNotFoundError(f"Band {band} not found in {folder}")


def read_band(path: Path) -> tuple[np.ndarray, dict, rasterio.Affine, object]:
    with rasterio.open(path) as src:
        array = src.read(1).astype("float32")
        profile = src.profile.copy()
        transform = src.transform
        crs = src.crs
        nodata = src.nodata

    if nodata is not None:
        array = np.where(array == nodata, np.nan, array)
    array = np.where(np.isfinite(array), array, np.nan)
    return array, profile, transform, crs


def safe_index(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    return np.divide(
        numerator,
        denominator,
        out=np.full_like(numerator, np.nan, dtype="float32"),
        where=np.abs(denominator) > 1e-6,
    )

