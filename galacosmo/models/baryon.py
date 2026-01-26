"""Baryonic component calculations for rotation curves."""

import numpy as np
from ..config.constants import ML_REF_DISK, ML_REF_BULGE


def baryon_components(
    Vdisk: np.ndarray,
    Vbul: np.ndarray,
    Vgas: np.ndarray,
    ml_disk: float = ML_REF_DISK,
    ml_bulge: float = ML_REF_BULGE,
) -> tuple:
    """
    Calculate baryonic velocity components with M/L scaling.

    The input velocities from SPARC are normalized to M/L = 1.
    This function applies the actual M/L ratios.

    Parameters
    ----------
    Vdisk : array-like
        Disk velocity component (M/L = 1 normalization)
    Vbul : array-like
        Bulge velocity component (M/L = 1 normalization)
    Vgas : array-like
        Gas velocity component
    ml_disk : float
        Disk mass-to-light ratio
    ml_bulge : float
        Bulge mass-to-light ratio

    Returns
    -------
    tuple
        (Vd, Vb, Vg, Vbar) - Scaled velocities and total baryonic velocity
    """
    # Sanitize inputs
    Vdisk = np.nan_to_num(Vdisk, nan=0.0, posinf=0.0, neginf=0.0)
    Vbul = np.nan_to_num(Vbul, nan=0.0, posinf=0.0, neginf=0.0)
    Vgas = np.nan_to_num(Vgas, nan=0.0, posinf=0.0, neginf=0.0)

    # M/L scaling factors (V proportional to sqrt(M) proportional to sqrt(M/L))
    scale_disk = np.sqrt(ml_disk / ML_REF_DISK) if ML_REF_DISK > 0 else 1.0
    scale_bulge = np.sqrt(ml_bulge / ML_REF_BULGE) if ML_REF_BULGE > 0 else 1.0

    # Apply scaling
    Vd = scale_disk * Vdisk
    Vb = scale_bulge * Vbul
    Vg = Vgas  # Gas doesn't need M/L scaling

    # Total baryonic velocity (sum in quadrature)
    Vbar = np.sqrt(np.clip(Vd**2 + Vb**2 + Vg**2, 0, None))

    return Vd, Vb, Vg, Vbar


def total_velocity(Vbar: np.ndarray, Vhalo: np.ndarray) -> np.ndarray:
    """
    Calculate total rotation velocity from baryonic and halo components.

    Parameters
    ----------
    Vbar : array-like
        Total baryonic velocity
    Vhalo : array-like
        Dark matter halo velocity

    Returns
    -------
    ndarray
        Total rotation velocity
    """
    Vbar = np.nan_to_num(Vbar, nan=0.0, posinf=0.0, neginf=0.0)
    Vhalo = np.nan_to_num(Vhalo, nan=0.0, posinf=0.0, neginf=0.0)
    return np.sqrt(np.clip(Vbar**2 + Vhalo**2, 0, None))
