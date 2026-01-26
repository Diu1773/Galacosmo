"""SN Ia data loaders for Hubble diagram analysis."""

import os
import re
import glob
import json
from pathlib import Path
from collections import Counter
from typing import Optional, List, Tuple, Dict

import pandas as pd
import numpy as np


# Default sample_id to paper_name mapping for Union2.1
DEFAULT_SAMPLE_MAPPING: Dict[int, str] = {
    1: "Hamuy et al. (1996)",
    2: "Krisciunas et al. (2005)",
    3: "Riess et al. (1999)",
    4: "Jha et al. (2006)",
    5: "Kowalski et al. (2008) (SCP)",
    6: "Hicken et al. (2009)",
    7: "Contreras et al. (2010)",
    8: "Holtzman et al. (2009)",
    9: "Riess et al. (1998) + HZT",
    10: "Perlmutter et al. (1999) (SCP)",
    11: "Barris et al. (2004)",
    12: "Amanullah et al. (2008) (SCP)",
    13: "Knop et al. (2003) (SCP)",
    14: "Astier et al. (2006)",
    15: "Miknaitis et al. (2007)",
    16: "Tonry et al. (2003)",
    17: "Riess et al. (2007)",
    18: "Amanullah et al. (2010) / SCP High-z 01",
    19: "Cluster Search (SCP) / HST Cluster Survey",
}


def load_sample_mapping(path: Optional[str] = None) -> Dict[int, str]:
    """
    Load sample_id to paper_name mapping from JSON file.

    Parameters
    ----------
    path : str, optional
        Path to JSON mapping file. Uses default mapping if not provided.

    Returns
    -------
    dict
        Mapping from sample_id (int) to paper_name (str)
    """
    if path is None:
        return DEFAULT_SAMPLE_MAPPING.copy()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Convert string keys to int
        return {int(k): v for k, v in data.items()}
    except Exception:
        return DEFAULT_SAMPLE_MAPPING.copy()


def _parse_value_with_error(s: str) -> Tuple[float, float]:
    """
    Parse a value with error in parentheses, e.g., '16.86(0.19)'.

    Returns
    -------
    tuple
        (value, error)
    """
    match = re.match(r"([-\d.]+)\(([\d.]+)\)", s.strip())
    if match:
        return float(match.group(1)), float(match.group(2))
    # Try plain number
    try:
        return float(s.strip()), 0.0
    except ValueError:
        return np.nan, np.nan


def load_union21_latex(
    path: str,
    mapping_path: Optional[str] = None,
    exclude_cuts_failed: bool = False,
) -> pd.DataFrame:
    """
    Load Union2.1 AllSNe.tex format data.

    The LaTeX table format is:
    SN_name & z & mB(err) & stretch(err) & color(err) & mu(err) & P_lowmass & sample & cuts\\

    Parameters
    ----------
    path : str
        Path to the .tex file
    mapping_path : str, optional
        Path to JSON file with sample_id to paper_name mapping
    exclude_cuts_failed : bool
        If True, exclude rows where cuts_failed is not empty/nodata

    Returns
    -------
    DataFrame
        Columns: name, z, mB, mB_err, stretch, stretch_err, color, color_err,
                 mu, emu, P_lowmass, sample_id, paper_name, cuts_failed
    """
    mapping = load_sample_mapping(mapping_path)

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("%"):
                continue
            # Remove trailing \\ and whitespace
            if line.endswith("\\\\"):
                line = line[:-2].strip()

            # Split by &
            parts = [p.strip() for p in line.split("&")]
            if len(parts) < 9:
                continue

            try:
                name = parts[0]
                z = float(parts[1])
                mB, mB_err = _parse_value_with_error(parts[2])
                stretch, stretch_err = _parse_value_with_error(parts[3])
                color, color_err = _parse_value_with_error(parts[4])
                mu, mu_err = _parse_value_with_error(parts[5])
                P_lowmass = float(parts[6])
                sample_id = int(parts[7])
                cuts = parts[8].replace("\\nodata", "").strip()

                # Get paper name from mapping
                paper_name = mapping.get(sample_id, f"Sample {sample_id}")

                rows.append({
                    "name": name,
                    "z": z,
                    "mB": mB,
                    "mB_err": mB_err,
                    "stretch": stretch,
                    "stretch_err": stretch_err,
                    "color": color,
                    "color_err": color_err,
                    "mu": mu,
                    "emu": mu_err,
                    "P_lowmass": P_lowmass,
                    "sample_id": sample_id,
                    "paper_name": paper_name,
                    "cuts_failed": cuts,
                })
            except (ValueError, IndexError):
                continue

    df = pd.DataFrame(rows)

    if exclude_cuts_failed and len(df) > 0:
        df = df[df["cuts_failed"] == ""].reset_index(drop=True)

    return df


def get_union21_by_sample(
    df: pd.DataFrame,
) -> Dict[int, pd.DataFrame]:
    """
    Split Union2.1 DataFrame by sample_id.

    Parameters
    ----------
    df : DataFrame
        Union2.1 data loaded by load_union21_latex

    Returns
    -------
    dict
        Mapping from sample_id to DataFrame subset
    """
    result = {}
    for sample_id in df["sample_id"].unique():
        result[sample_id] = df[df["sample_id"] == sample_id].reset_index(drop=True)
    return result


def load_sn_table(path: str) -> pd.DataFrame:
    """
    Load SN Ia distance modulus data with flexible format detection.

    Supports various formats:
    - 3 columns: z, mu, error
    - 4 columns: name, z, mu, error
    - 5 columns: name, z, mu, sigma_stat, sigma_sys
    - 6 columns: name, z, mu, sigma_stat, sigma_sys, sample

    Parameters
    ----------
    path : str
        Path to data file

    Returns
    -------
    DataFrame
        Standardized data with columns: z, mu, emu
    """
    # Try pandas first
    try:
        df = pd.read_csv(
            path,
            sep=r"\s+|,",
            engine="python",
            comment="#",
            header=None,
            on_bad_lines="skip",
        )
    except Exception:
        df = None

    # Fall back to manual parsing
    if df is None or df.shape[1] <= 1:
        rows = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = re.split(r"[,\s]+", line)
                if parts:
                    rows.append(parts)

        if not rows:
            raise ValueError(f"File is empty or unparseable: {path}")

        # Find most common column count
        n_cols = Counter(len(r) for r in rows).most_common(1)[0][0]
        rows = [r[:n_cols] for r in rows if len(r) >= n_cols]
        df = pd.DataFrame(rows)

    # Assign column names based on count
    n = df.shape[1]
    if n == 3:
        df.columns = ["z", "mu", "emu"]
    elif n == 4:
        df.columns = ["name", "z", "mu", "emu"]
    elif n == 5:
        df.columns = ["name", "z", "mu", "sigma_stat", "sigma_sys"]
    else:
        df = df.iloc[:, :6].copy()
        df.columns = ["name", "z", "mu", "sigma_stat", "sigma_sys", "sample"]

    # Build output DataFrame
    out = pd.DataFrame()
    out["z"] = pd.to_numeric(df.get("z"), errors="coerce")
    out["mu"] = pd.to_numeric(df.get("mu"), errors="coerce")

    if "emu" in df.columns:
        out["emu"] = pd.to_numeric(df["emu"], errors="coerce")
    else:
        # Combine stat and sys errors
        stat = pd.to_numeric(df.get("sigma_stat"), errors="coerce")
        sys = pd.to_numeric(df.get("sigma_sys"), errors="coerce")
        out["emu"] = np.sqrt(stat**2 + sys**2)

    # Keep name if available
    if "name" in df.columns:
        out["name"] = df["name"]

    # Clean up
    out = out.dropna(subset=["z", "mu"])
    out = out[out["z"] > 0].reset_index(drop=True)

    return out


def load_sn_directory(directory: str) -> List[Tuple[str, pd.DataFrame]]:
    """
    Load all SN Ia data files from a directory.

    Parameters
    ----------
    directory : str
        Directory containing data files

    Returns
    -------
    list
        List of (filename, DataFrame) tuples
    """
    patterns = ["*.txt", "*.dat", "*.csv"]
    results = []

    for pattern in patterns:
        for path in sorted(glob.glob(os.path.join(directory, pattern))):
            try:
                df = load_sn_table(path)
                if len(df) > 0:
                    results.append((os.path.basename(path), df))
            except Exception:
                continue

    return results


def compute_chi2(
    z: np.ndarray,
    mu_obs: np.ndarray,
    mu_err: np.ndarray,
    mu_theory: np.ndarray,
) -> Tuple[float, float, int]:
    """
    Compute chi-squared statistic.

    Parameters
    ----------
    z : array-like
        Redshift
    mu_obs : array-like
        Observed distance modulus
    mu_err : array-like
        Distance modulus errors
    mu_theory : array-like
        Theoretical distance modulus

    Returns
    -------
    tuple
        (chi2, reduced_chi2, dof)
    """
    # Clean data
    valid = np.isfinite(mu_obs) & np.isfinite(mu_theory) & (mu_err > 0)
    if not np.any(valid):
        return np.nan, np.nan, 0

    residuals = (mu_obs[valid] - mu_theory[valid]) / mu_err[valid]
    chi2 = float(np.sum(residuals**2))
    dof = int(np.sum(valid)) - 1  # 1 free parameter (H0)
    reduced = chi2 / max(dof, 1)

    return chi2, reduced, dof


class SNIaDataset:
    """Manager for multiple SN Ia datasets."""

    def __init__(self):
        self.datasets = {}
        self._style_idx = 0

    def add_file(self, path: str, label: Optional[str] = None) -> str:
        """
        Add a data file.

        Parameters
        ----------
        path : str
            Path to data file
        label : str, optional
            Dataset label (uses filename if not provided)

        Returns
        -------
        str
            The label used for this dataset
        """
        if label is None:
            label = os.path.basename(path)

        # Handle duplicate labels
        if label in self.datasets:
            base = label
            k = 2
            while label in self.datasets:
                label = f"{base} ({k})"
                k += 1

        df = load_sn_table(path)
        self.datasets[label] = {
            "df": df,
            "path": path,
            "enabled": False,
        }
        return label

    def add_directory(self, directory: str) -> List[str]:
        """
        Add all data files from a directory.

        Returns
        -------
        list
            Labels of added datasets
        """
        added = []
        for label, df in load_sn_directory(directory):
            if label in self.datasets:
                base = label
                k = 2
                while label in self.datasets:
                    label = f"{base} ({k})"
                    k += 1

            self.datasets[label] = {
                "df": df,
                "path": os.path.join(directory, label),
                "enabled": False,
            }
            added.append(label)
        return added

    def remove(self, label: str):
        """Remove a dataset."""
        if label in self.datasets:
            del self.datasets[label]

    def clear(self):
        """Remove all datasets."""
        self.datasets.clear()

    def get_enabled(self) -> List[Tuple[str, pd.DataFrame]]:
        """Get list of enabled datasets."""
        return [
            (label, data["df"])
            for label, data in self.datasets.items()
            if data.get("enabled", False)
        ]

    def set_enabled(self, label: str, enabled: bool):
        """Enable or disable a dataset."""
        if label in self.datasets:
            self.datasets[label]["enabled"] = enabled

    @property
    def labels(self) -> List[str]:
        """List of all dataset labels."""
        return list(self.datasets.keys())

    def __len__(self) -> int:
        return len(self.datasets)
