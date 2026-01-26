"""Dark matter halo models for rotation curve fitting."""

import numpy as np
from ..config.constants import G, DEFAULT_H0


def v_halo_iso(r: np.ndarray, rho0: float, rc: float) -> np.ndarray:
    """
    Isothermal sphere halo velocity profile.

    Parameters
    ----------
    r : array-like
        Radii in kpc
    rho0 : float
        Central density in M_sun/kpc^3
    rc : float
        Core radius in kpc

    Returns
    -------
    ndarray
        Circular velocity in km/s
    """
    r = np.asarray(r, dtype=float)
    r_safe = np.where(r <= 0, 1e-6, r)
    term = 1.0 - (rc / r_safe) * np.arctan(r_safe / rc)
    return np.sqrt(4 * np.pi * G * rho0 * rc**2 * term)


def v_halo_nfw(
    r: np.ndarray,
    V200: float,
    c: float,
    H0: float = DEFAULT_H0,
    z: float = 0.0,
    Omega_m: float = 0.315,
    Omega_L: float = 0.685,
    use_Hz: bool = False,
) -> np.ndarray:
    """
    NFW (Navarro-Frenk-White) halo velocity profile.

    Parameters
    ----------
    r : array-like
        Radii in kpc
    V200 : float
        Circular velocity at R200 in km/s
    c : float
        Concentration parameter
    H0 : float
        Hubble constant in km/s/Mpc
    z : float
        Redshift (used if use_Hz=True)
    Omega_m : float
        Matter density parameter
    Omega_L : float
        Dark energy density parameter
    use_Hz : bool
        If True, use H(z) instead of H0

    Returns
    -------
    ndarray
        Circular velocity in km/s
    """
    r = np.asarray(r, dtype=float)

    # Calculate H (optionally with redshift)
    if use_Hz and z > 0:
        Omega_k = 1.0 - Omega_m - Omega_L
        E_z = np.sqrt(Omega_m * (1 + z) ** 3 + Omega_k * (1 + z) ** 2 + Omega_L)
        H = H0 * E_z
    else:
        H = H0

    # Convert H to kpc units
    H_kpc = H / 1000.0  # km/s/kpc

    # R200 from V200 = 10 * H * R200
    R200 = V200 / (10.0 * H_kpc)
    rs = R200 / c

    x = np.maximum(r / rs, 1e-8)
    g = np.log(1 + c) - c / (1 + c)
    fx = (np.log(1 + x) - x / (1 + x)) / (x * g)

    return np.sqrt(np.clip(V200**2 * fx, 0, None))


def halo_velocity(
    r: np.ndarray,
    p1: float,
    p2: float,
    model: str = "ISO",
    **kwargs,
) -> np.ndarray:
    """
    Compute halo circular velocity for specified model.

    Parameters
    ----------
    r : array-like
        Radii in kpc
    p1, p2 : float
        Model parameters:
        - ISO: rho0 (M_sun/kpc^3), rc (kpc)
        - NFW: V200 (km/s), c (dimensionless)
    model : str
        Halo model type ("ISO" or "NFW")
    **kwargs
        Additional arguments for NFW (H0, z, Omega_m, Omega_L, use_Hz)

    Returns
    -------
    ndarray
        Circular velocity in km/s
    """
    if model.upper() == "ISO":
        return v_halo_iso(r, p1, p2)
    else:
        return v_halo_nfw(r, p1, p2, **kwargs)


def get_halo_param_names(model: str) -> tuple:
    """Get parameter names for a halo model."""
    if model.upper() == "ISO":
        return ("rho0", "rc")
    else:
        return ("V200", "c")


def get_halo_param_units(model: str) -> tuple:
    """Get parameter units for a halo model."""
    if model.upper() == "ISO":
        return ("M_sun/kpc^3", "kpc")
    else:
        return ("km/s", "")
