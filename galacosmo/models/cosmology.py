"""Cosmological calculations with caching for performance."""

import numpy as np
from functools import lru_cache
from typing import Tuple, Optional
from scipy.integrate import quad

from ..config.constants import C_KM_S, DEFAULT_H0, DEFAULT_OMEGA_M, DEFAULT_OMEGA_L


def E_of_z(
    z: np.ndarray,
    Omega_m: float = DEFAULT_OMEGA_M,
    Omega_L: float = DEFAULT_OMEGA_L,
) -> np.ndarray:
    """
    Dimensionless Hubble parameter E(z) = H(z)/H0.

    Parameters
    ----------
    z : array-like
        Redshift
    Omega_m : float
        Matter density parameter
    Omega_L : float
        Dark energy density parameter

    Returns
    -------
    ndarray
        E(z) values
    """
    z = np.atleast_1d(z).astype(float)
    Omega_k = 1.0 - Omega_m - Omega_L
    return np.sqrt(Omega_m * (1 + z) ** 3 + Omega_k * (1 + z) ** 2 + Omega_L)


@lru_cache(maxsize=64)
def _comoving_distance_single(
    z: float,
    Omega_m: float,
    Omega_L: float,
    H0: float,
) -> float:
    """Cached comoving distance calculation for a single z value."""
    if z <= 0:
        return 0.0

    def integrand(zp):
        Omega_k = 1.0 - Omega_m - Omega_L
        E = np.sqrt(Omega_m * (1 + zp) ** 3 + Omega_k * (1 + zp) ** 2 + Omega_L)
        return 1.0 / E

    result, _ = quad(integrand, 0, z)
    return (C_KM_S / H0) * result


def comoving_distance(
    z: np.ndarray,
    Omega_m: float = DEFAULT_OMEGA_M,
    Omega_L: float = DEFAULT_OMEGA_L,
    H0: float = DEFAULT_H0,
) -> np.ndarray:
    """
    Comoving distance in Mpc.

    Parameters
    ----------
    z : array-like
        Redshift
    Omega_m : float
        Matter density parameter
    Omega_L : float
        Dark energy density parameter
    H0 : float
        Hubble constant in km/s/Mpc

    Returns
    -------
    ndarray
        Comoving distance in Mpc
    """
    z = np.atleast_1d(z).astype(float)

    # Round parameters for better cache hits
    Om_key = round(Omega_m, 4)
    Ol_key = round(Omega_L, 4)
    H0_key = round(H0, 2)

    dc = np.array([
        _comoving_distance_single(float(zi), Om_key, Ol_key, H0_key)
        for zi in z
    ])
    return dc


def luminosity_distance(
    z: np.ndarray,
    Omega_m: float = DEFAULT_OMEGA_M,
    Omega_L: float = DEFAULT_OMEGA_L,
    H0: float = DEFAULT_H0,
) -> np.ndarray:
    """
    Luminosity distance in Mpc.

    Parameters
    ----------
    z : array-like
        Redshift
    Omega_m : float
        Matter density parameter
    Omega_L : float
        Dark energy density parameter
    H0 : float
        Hubble constant in km/s/Mpc

    Returns
    -------
    ndarray
        Luminosity distance in Mpc
    """
    z = np.atleast_1d(z).astype(float)
    Omega_k = 1.0 - Omega_m - Omega_L

    DC = comoving_distance(z, Omega_m, Omega_L, H0)

    # Transverse comoving distance (depends on curvature)
    if np.isclose(Omega_k, 0.0, atol=1e-6):
        DM = DC
    elif Omega_k > 0:
        # Open universe
        sqrt_Ok = np.sqrt(Omega_k)
        DM = (C_KM_S / H0) / sqrt_Ok * np.sinh(sqrt_Ok * DC * (H0 / C_KM_S))
    else:
        # Closed universe
        sqrt_Ok = np.sqrt(-Omega_k)
        DM = (C_KM_S / H0) / sqrt_Ok * np.sin(sqrt_Ok * DC * (H0 / C_KM_S))

    return (1.0 + z) * DM


def mu_theory(
    z: np.ndarray,
    Omega_m: float = DEFAULT_OMEGA_M,
    Omega_L: float = DEFAULT_OMEGA_L,
    H0: float = DEFAULT_H0,
) -> np.ndarray:
    """
    Distance modulus (mu = m - M).

    Parameters
    ----------
    z : array-like
        Redshift
    Omega_m : float
        Matter density parameter
    Omega_L : float
        Dark energy density parameter
    H0 : float
        Hubble constant in km/s/Mpc

    Returns
    -------
    ndarray
        Distance modulus in magnitudes
    """
    DL = luminosity_distance(np.asarray(z, float), Omega_m, Omega_L, H0)
    return 5.0 * np.log10(np.clip(DL, 1e-12, None)) + 25.0


def dl_from_mu(mu: np.ndarray) -> np.ndarray:
    """
    Convert distance modulus to luminosity distance.

    Parameters
    ----------
    mu : array-like
        Distance modulus in magnitudes

    Returns
    -------
    ndarray
        Luminosity distance in Mpc
    """
    return 10 ** ((np.asarray(mu) - 25.0) / 5.0)


def clear_cache():
    """Clear the cosmology calculation cache."""
    _comoving_distance_single.cache_clear()


def get_cache_info():
    """Get cache statistics."""
    return _comoving_distance_single.cache_info()


# Pre-computed grids for fast interpolation
class CosmoGrid:
    """Pre-computed cosmology grid for fast interpolation."""

    def __init__(
        self,
        z_min: float = 0.001,
        z_max: float = 2.0,
        n_points: int = 1000,
        Omega_m: float = DEFAULT_OMEGA_M,
        Omega_L: float = DEFAULT_OMEGA_L,
        H0: float = DEFAULT_H0,
    ):
        self.z_grid = np.logspace(np.log10(z_min), np.log10(z_max), n_points)
        self.Omega_m = Omega_m
        self.Omega_L = Omega_L
        self.H0 = H0
        self._compute()

    def _compute(self):
        """Compute grid values."""
        self.mu_grid = mu_theory(self.z_grid, self.Omega_m, self.Omega_L, self.H0)
        self.dl_grid = luminosity_distance(
            self.z_grid, self.Omega_m, self.Omega_L, self.H0
        )

    def mu_interp(self, z: np.ndarray) -> np.ndarray:
        """Interpolate distance modulus."""
        return np.interp(z, self.z_grid, self.mu_grid)

    def dl_interp(self, z: np.ndarray) -> np.ndarray:
        """Interpolate luminosity distance."""
        return np.interp(z, self.z_grid, self.dl_grid)
