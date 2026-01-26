"""Curve fitting utilities for rotation curves."""

import numpy as np
from scipy.optimize import curve_fit
from typing import Tuple, Optional

from .halo import halo_velocity
from .baryon import total_velocity
from ..config.constants import HALO_BOUNDS


def fit_halo(
    R: np.ndarray,
    Vobs: np.ndarray,
    e_Vobs: np.ndarray,
    Vbar: np.ndarray,
    model: str = "ISO",
    **halo_kwargs,
) -> Tuple[float, float]:
    """
    Fit dark matter halo parameters to observed rotation curve.

    Parameters
    ----------
    R : array-like
        Radii in kpc
    Vobs : array-like
        Observed rotation velocities in km/s
    e_Vobs : array-like
        Velocity uncertainties in km/s
    Vbar : array-like
        Total baryonic velocity in km/s
    model : str
        Halo model ("ISO" or "NFW")
    **halo_kwargs
        Additional arguments for halo model (H0, z, etc.)

    Returns
    -------
    tuple
        (p1, p2) - Fitted halo parameters
    """
    model = model.upper()
    bounds_config = HALO_BOUNDS.get(model, HALO_BOUNDS["ISO"])

    if model == "ISO":
        p0 = [
            bounds_config["rho0"]["init"],
            max(0.5, np.nanmedian(R)),
        ]
        bounds = (
            [bounds_config["rho0"]["min"], bounds_config["rc"]["min"]],
            [bounds_config["rho0"]["max"], bounds_config["rc"]["max"]],
        )
    else:  # NFW
        p0 = [
            bounds_config["V200"]["init"],
            bounds_config["c"]["init"],
        ]
        bounds = (
            [bounds_config["V200"]["min"], bounds_config["c"]["min"]],
            [bounds_config["V200"]["max"], bounds_config["c"]["max"]],
        )

    # Clean and filter inputs
    R = np.asarray(R, dtype=float)
    Vobs = np.asarray(Vobs, dtype=float)
    Vbar = np.asarray(Vbar, dtype=float)
    e_Vobs = np.asarray(e_Vobs, dtype=float)

    use_sigma = np.any(np.isfinite(e_Vobs) & (e_Vobs > 0))
    valid = np.isfinite(R) & np.isfinite(Vobs) & np.isfinite(Vbar)
    if use_sigma:
        valid &= np.isfinite(e_Vobs) & (e_Vobs > 0)

    R_fit = R[valid]
    Vobs_fit = Vobs[valid]
    Vbar_fit = Vbar[valid]
    sigma_fit = e_Vobs[valid] if use_sigma else None

    if len(R_fit) < 3:
        return p0[0], p0[1]

    def model_total(r, p1, p2):
        Vh = halo_velocity(r, p1, p2, model, **halo_kwargs)
        return total_velocity(Vbar_fit, Vh)

    try:
        popt, pcov = curve_fit(
            model_total,
            R_fit,
            Vobs_fit,
            p0=p0,
            sigma=sigma_fit,
            absolute_sigma=True if sigma_fit is not None else False,
            bounds=bounds,
            maxfev=60000,
        )
        return popt[0], popt[1]
    except Exception as e:
        # Return initial guesses on failure
        return p0[0], p0[1]


def compute_rotation_curves(
    R: np.ndarray,
    Vobs: np.ndarray,
    e_Vobs: np.ndarray,
    Vdisk: np.ndarray,
    Vbul: np.ndarray,
    Vgas: np.ndarray,
    ml_disk: float,
    ml_bulge: float,
    model: str = "ISO",
    n_interp: int = 400,
    **halo_kwargs,
) -> dict:
    """
    Compute all rotation curve components.

    Parameters
    ----------
    R : array-like
        Radii in kpc
    Vobs : array-like
        Observed velocities in km/s
    e_Vobs : array-like
        Velocity uncertainties in km/s
    Vdisk, Vbul, Vgas : array-like
        Baryonic component velocities
    ml_disk, ml_bulge : float
        Mass-to-light ratios
    model : str
        Halo model
    n_interp : int
        Number of interpolation points
    **halo_kwargs
        Additional halo model arguments

    Returns
    -------
    dict
        Dictionary with all curve data
    """
    from .baryon import baryon_components

    # Calculate baryonic components at observed radii
    Vd, Vb, Vg, Vbar = baryon_components(Vdisk, Vbul, Vgas, ml_disk, ml_bulge)

    # Fit halo
    p1, p2 = fit_halo(R, Vobs, e_Vobs, Vbar, model, **halo_kwargs)

    # Interpolation grid
    r_min = max(1e-3, np.nanmin(R) * 0.7)
    r_max = np.nanmax(R) * 1.15
    r = np.linspace(r_min, r_max, n_interp)

    # Interpolate baryonic components
    Vd_i = np.interp(r, R, np.nan_to_num(Vd, nan=0.0))
    Vb_i = np.interp(r, R, np.nan_to_num(Vb, nan=0.0))
    Vg_i = np.interp(r, R, np.nan_to_num(Vg, nan=0.0))
    Vbar_i = np.sqrt(np.clip(Vd_i**2 + Vb_i**2 + Vg_i**2, 0, None))

    # Halo and total at observed radii
    Vh_obs = halo_velocity(R, p1, p2, model, **halo_kwargs)
    Vtot_obs = total_velocity(Vbar, Vh_obs)

    # Halo and total on interpolation grid
    Vh_i = halo_velocity(r, p1, p2, model, **halo_kwargs)
    Vtot_i = total_velocity(Vbar_i, Vh_i)

    return {
        # Observed data
        "R": R,
        "Vobs": Vobs,
        "eV": e_Vobs,
        # Interpolation grid
        "r": r,
        # Components
        "Vd": Vd_i,
        "Vb": Vb_i,
        "Vg": Vg_i,
        "Vbar": Vbar_i,
        "Vh": Vh_i,
        "Vtot": Vtot_i,
        "Vtot_obs": Vtot_obs,
        "Vbar_obs": Vbar,
        # Fit parameters
        "params": (p1, p2),
        "model": model,
    }
