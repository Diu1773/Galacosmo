"""SPARC data loaders for galaxy rotation curves."""

import os
import re
import glob
from pathlib import Path
from typing import Optional, Tuple, List

import pandas as pd
import numpy as np


# Default column names for SPARC tables
TABLE1_COLUMNS = [
    "Galaxy", "T", "D", "e_D", "f_D", "Inc", "e_Inc", "L36", "e_L36",
    "Reff", "SBeff", "Rdisk", "SBdisk", "MHI", "RHI", "Vflat", "e_Vflat", "Q", "Ref"
]

TABLE2_COLUMNS = [
    "ID", "D", "R", "Vobs", "e_Vobs", "Vgas", "Vdisk", "Vbul", "SBdisk", "SBbul"
]


def find_sparc_files(directory: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Find SPARC Table1 and Table2 files in a directory.

    Parameters
    ----------
    directory : str
        Directory to search

    Returns
    -------
    tuple
        (table1_path, table2_path) or (None, None) if not found
    """
    table1_patterns = ["*Table1*.mrt", "*Table1*.txt", "*table1*.txt"]
    table2_patterns = [
        "*Table2*.mrt", "*Table2*.txt", "*table2*.txt",
        "*Mass*Models*.mrt", "*Mass*Models*.txt"
    ]

    table1_path = None
    table2_path = None

    for pattern in table1_patterns:
        matches = sorted(glob.glob(os.path.join(directory, pattern)))
        if matches:
            table1_path = matches[0]
            break

    for pattern in table2_patterns:
        matches = sorted(glob.glob(os.path.join(directory, pattern)))
        if matches:
            table2_path = matches[0]
            break

    return table1_path, table2_path


def read_table1(path: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Read SPARC Table1 (galaxy sample information).

    Parameters
    ----------
    path : str
        Path to Table1 file
    columns : list, optional
        Column names (uses default SPARC columns if not provided)

    Returns
    -------
    DataFrame
        Galaxy sample data
    """
    cols = columns or TABLE1_COLUMNS

    # Try fixed-width format first
    try:
        df = pd.read_fwf(path, comment="#", names=cols)
    except Exception:
        # Fall back to whitespace-separated
        df = pd.read_csv(path, sep=r"\s+", comment="#", names=cols, engine="python")

    # Clean up
    df = df.dropna(subset=["Galaxy"]).copy()
    df["Galaxy"] = df["Galaxy"].astype(str).str.strip()

    return df


def read_table2(
    path: str,
    galaxy_name: Optional[str] = None,
    columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Read SPARC Table2 (rotation curve data).

    Parameters
    ----------
    path : str
        Path to Table2 file
    galaxy_name : str, optional
        Filter by galaxy name
    columns : list, optional
        Column names (uses default SPARC columns if not provided)

    Returns
    -------
    DataFrame
        Rotation curve data
    """
    cols = columns or TABLE2_COLUMNS

    df = pd.read_csv(
        path,
        sep=r"\s+",
        comment="#",
        names=cols,
        engine="python",
        dtype=str,
    )

    if galaxy_name is not None:
        # Filter by galaxy name
        galaxy_clean = galaxy_name.strip().lower()
        mask = df["ID"].astype(str).str.strip().str.lower() == galaxy_clean

        if not mask.any():
            # Try partial match
            mask = df["ID"].astype(str).str.contains(
                re.escape(galaxy_name), case=False, na=False
            )

        if not mask.any():
            raise ValueError(f"Galaxy '{galaxy_name}' not found in Table2")

        df = df[mask].copy()

    # Convert numeric columns
    numeric_cols = [
        "D",
        "R",
        "Vobs",
        "e_Vobs",
        "Vgas",
        "Vdisk",
        "Vbul",
        "SBdisk",
        "SBbul",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fill NaN in velocity components with 0
    fill_cols = ["Vgas", "Vdisk", "Vbul", "e_Vobs"]
    for col in fill_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0.0)

    # Drop rows without essential data
    df = df.dropna(subset=["R", "Vobs"]).sort_values("R")

    return df.reset_index(drop=True)


def get_galaxy_list(table1_df: pd.DataFrame) -> List[str]:
    """Get list of galaxy names from Table1."""
    return table1_df["Galaxy"].tolist()


def get_galaxy_info(table1_df: pd.DataFrame, galaxy_name: str) -> dict:
    """
    Get information for a specific galaxy.

    Parameters
    ----------
    table1_df : DataFrame
        Table1 data
    galaxy_name : str
        Galaxy name

    Returns
    -------
    dict
        Galaxy properties
    """
    mask = table1_df["Galaxy"].str.lower() == galaxy_name.lower()
    if not mask.any():
        raise ValueError(f"Galaxy '{galaxy_name}' not found")

    row = table1_df[mask].iloc[0]
    return {
        "name": row["Galaxy"],
        "distance": row.get("D", None),
        "inclination": row.get("Inc", None),
        "luminosity": row.get("L36", None),
        "HI_mass": row.get("MHI", None),
        "Vflat": row.get("Vflat", None),
    }


class SPARCDataset:
    """Convenience class for working with SPARC data."""

    def __init__(self, directory: str):
        """
        Initialize SPARC dataset from a directory.

        Parameters
        ----------
        directory : str
            Directory containing SPARC data files
        """
        self.directory = directory
        self.table1_path, self.table2_path = find_sparc_files(directory)

        if not self.table1_path or not self.table2_path:
            raise FileNotFoundError(
                f"Could not find SPARC data files in {directory}"
            )

        self.table1 = read_table1(self.table1_path)
        self._current_galaxy = None
        self._current_data = None

    @property
    def galaxies(self) -> List[str]:
        """List of available galaxies."""
        return get_galaxy_list(self.table1)

    def get_rotation_curve(self, galaxy_name: str) -> pd.DataFrame:
        """Get rotation curve data for a galaxy."""
        if self._current_galaxy != galaxy_name:
            self._current_data = read_table2(self.table2_path, galaxy_name)
            self._current_galaxy = galaxy_name
        return self._current_data

    def get_info(self, galaxy_name: str) -> dict:
        """Get galaxy information."""
        return get_galaxy_info(self.table1, galaxy_name)
