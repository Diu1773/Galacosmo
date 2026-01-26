"""Data loaders for GalaCosmo."""

from .sparc_loader import read_table1, read_table2, find_sparc_files
from .snia_loader import (
    load_sn_table,
    load_union21_latex,
    load_sample_mapping,
    get_union21_by_sample,
    DEFAULT_SAMPLE_MAPPING,
)
