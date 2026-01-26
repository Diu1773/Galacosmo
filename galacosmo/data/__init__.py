"""Data loaders for GalaCosmo."""

from pathlib import Path

from .sparc_loader import read_table1, read_table2, find_sparc_files
from .snia_loader import (
    load_sn_table,
    load_union21_latex,
    load_sample_mapping,
    get_union21_by_sample,
    DEFAULT_SAMPLE_MAPPING,
)


def get_default_data_dir() -> Path | None:
    """Return the repo-level data directory if present."""
    try:
        repo_root = Path(__file__).resolve().parents[2]
    except IndexError:
        return None
    data_dir = repo_root / "data"
    return data_dir if data_dir.exists() else None


__all__ = [
    "read_table1",
    "read_table2",
    "find_sparc_files",
    "load_sn_table",
    "load_union21_latex",
    "load_sample_mapping",
    "get_union21_by_sample",
    "DEFAULT_SAMPLE_MAPPING",
    "get_default_data_dir",
]
