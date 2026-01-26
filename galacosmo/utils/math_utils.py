"""Mathematical utilities for data processing."""

import numpy as np
import pandas as pd
from typing import Optional, Union, List


def smart_downsample(
    df: pd.DataFrame,
    max_points: int,
    key: str = "z",
    method: str = "density",
    use_log: bool = True,
) -> pd.DataFrame:
    """
    Smart downsampling of data to reduce rendering load.

    Parameters
    ----------
    df : DataFrame
        Input data
    max_points : int
        Maximum number of points to keep
    key : str
        Column to use for sampling distribution
    method : str
        Sampling method:
        - "uniform": Uniform spacing
        - "log_uniform": Uniform in log space
        - "density": Density-based (keeps more points in sparse regions)
    use_log : bool
        Use log scale for key column

    Returns
    -------
    DataFrame
        Downsampled data
    """
    if df is None or len(df) == 0 or max_points >= len(df):
        return df

    df = df.dropna(subset=[key]).copy()
    if len(df) == 0:
        return df

    df = df.sort_values(key).reset_index(drop=True)
    x = df[key].to_numpy(float)

    if method == "density":
        return _downsample_density(df, x, max_points, use_log)
    elif method == "log_uniform":
        return _downsample_log_uniform(df, x, max_points)
    else:  # uniform
        return _downsample_uniform(df, x, max_points, use_log)


def _downsample_uniform(
    df: pd.DataFrame,
    x: np.ndarray,
    n: int,
    use_log: bool = False,
) -> pd.DataFrame:
    """Uniform downsampling."""
    if use_log:
        x_work = np.log10(np.clip(x, 1e-12, None))
    else:
        x_work = x

    # Create uniform target points
    x_target = np.linspace(x_work.min(), x_work.max(), n)

    # Find closest points
    idx = np.clip(
        np.round(np.interp(x_target, x_work, np.arange(len(x_work)))).astype(int),
        0,
        len(x_work) - 1,
    )
    idx = np.unique(idx)

    return df.iloc[idx].reset_index(drop=True)


def _downsample_log_uniform(
    df: pd.DataFrame,
    x: np.ndarray,
    n: int,
) -> pd.DataFrame:
    """Uniform downsampling in log space."""
    x_log = np.log10(np.clip(x, 1e-12, None))
    x_target = np.linspace(x_log.min(), x_log.max(), n)

    idx = np.clip(
        np.round(np.interp(x_target, x_log, np.arange(len(x_log)))).astype(int),
        0,
        len(x_log) - 1,
    )
    idx = np.unique(idx)

    return df.iloc[idx].reset_index(drop=True)


def _downsample_density(
    df: pd.DataFrame,
    x: np.ndarray,
    n: int,
    use_log: bool = True,
) -> pd.DataFrame:
    """
    Density-based downsampling.
    Keeps more points in regions with sparse data.
    """
    if use_log:
        x_work = np.log10(np.clip(x, 1e-12, None))
    else:
        x_work = x

    # Estimate density using histogram
    n_bins = min(50, len(x_work) // 5)
    if n_bins < 2:
        return _downsample_uniform(df, x, n, use_log)

    hist, edges = np.histogram(x_work, bins=n_bins)
    bin_idx = np.digitize(x_work, edges[:-1]) - 1
    bin_idx = np.clip(bin_idx, 0, len(hist) - 1)

    # Weight inversely by density
    density = hist[bin_idx].astype(float)
    density = np.maximum(density, 1)
    weights = 1.0 / density
    weights /= weights.sum()

    # Sample with weights
    rng = np.random.default_rng(42)  # Reproducible
    idx = rng.choice(len(df), size=min(n, len(df)), replace=False, p=weights)
    idx = np.sort(idx)

    return df.iloc[idx].reset_index(drop=True)


def allocate_points(
    datasets: List[tuple],
    max_total: int,
) -> dict:
    """
    Allocate display points proportionally across datasets.

    Parameters
    ----------
    datasets : list
        List of (label, DataFrame) tuples
    max_total : int
        Maximum total points to display

    Returns
    -------
    dict
        {label: n_points} allocation
    """
    if not datasets:
        return {}

    total = sum(len(df) for _, df in datasets)
    if total <= max_total:
        return {label: len(df) for label, df in datasets}

    # Proportional allocation
    alloc = {}
    for label, df in datasets:
        n = max(1, int(round(max_total * len(df) / total)))
        alloc[label] = n

    # Adjust to hit exact total
    diff = max_total - sum(alloc.values())
    if diff != 0:
        # Add/remove from largest datasets first
        sorted_labels = sorted(alloc.keys(), key=lambda k: alloc[k], reverse=True)
        i = 0
        while diff != 0:
            label = sorted_labels[i % len(sorted_labels)]
            if diff > 0:
                alloc[label] += 1
                diff -= 1
            elif alloc[label] > 1:
                alloc[label] -= 1
                diff += 1
            i += 1
            if i > len(sorted_labels) * 10:
                break

    return alloc


def interpolate_curve(
    x: np.ndarray,
    y: np.ndarray,
    x_new: np.ndarray,
    fill_value: float = 0.0,
) -> np.ndarray:
    """
    Safe interpolation with NaN handling.

    Parameters
    ----------
    x : array-like
        Original x values
    y : array-like
        Original y values
    x_new : array-like
        New x values to interpolate at
    fill_value : float
        Value to use for NaN

    Returns
    -------
    ndarray
        Interpolated y values
    """
    y_clean = np.nan_to_num(y, nan=fill_value, posinf=fill_value, neginf=fill_value)
    return np.interp(x_new, x, y_clean)


def moving_average(x: np.ndarray, window: int = 5) -> np.ndarray:
    """Simple moving average smoothing."""
    if len(x) < window:
        return x
    return np.convolve(x, np.ones(window) / window, mode="same")
