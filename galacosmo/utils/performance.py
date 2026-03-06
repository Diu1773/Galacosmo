"""Performance optimization utilities."""

import numpy as np
from functools import lru_cache
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    size: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class CosmoCache:
    """
    Cache for pre-computed cosmology curves.

    Stores mu(z) curves for different parameter combinations
    to avoid repeated expensive calculations.
    """

    def __init__(self, max_size: int = 32):
        self.max_size = max_size
        self._cache = {}
        self._access_order = []
        self.stats = CacheStats()

    def _make_key(
        self,
        Omega_m: float,
        Omega_L: float,
        H0: float,
        z_min: float,
        z_max: float,
        n_points: int,
    ) -> tuple:
        """Create cache key from parameters."""
        return (
            round(Omega_m, 4),
            round(Omega_L, 4),
            round(H0, 1),
            round(z_min, 6),
            round(z_max, 6),
            int(n_points),
        )

    def get(
        self,
        Omega_m: float,
        Omega_L: float,
        H0: float,
        z_min: float,
        z_max: float,
        n_points: int,
    ) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Get cached curve if available.

        Returns
        -------
        tuple or None
            (z_grid, mu_grid) if cached, None otherwise
        """
        key = self._make_key(Omega_m, Omega_L, H0, z_min, z_max, n_points)
        if key in self._cache:
            self.stats.hits += 1
            # Move to end (most recently used)
            self._access_order.remove(key)
            self._access_order.append(key)
            return self._cache[key]
        self.stats.misses += 1
        return None

    def put(
        self,
        Omega_m: float,
        Omega_L: float,
        H0: float,
        z_min: float,
        z_max: float,
        n_points: int,
        z_grid: np.ndarray,
        mu_grid: np.ndarray,
    ):
        """Store a curve in cache."""
        key = self._make_key(Omega_m, Omega_L, H0, z_min, z_max, n_points)

        # Evict oldest if at capacity
        while len(self._cache) >= self.max_size:
            oldest = self._access_order.pop(0)
            del self._cache[oldest]

        self._cache[key] = (z_grid.copy(), mu_grid.copy())
        self._access_order.append(key)
        self.stats.size = len(self._cache)

    def get_or_compute(
        self,
        Omega_m: float,
        Omega_L: float,
        H0: float,
        z_min: float = 0.001,
        z_max: float = 2.0,
        n_points: int = 500,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get cached curve or compute and cache it.

        Parameters
        ----------
        Omega_m, Omega_L, H0 : float
            Cosmological parameters
        z_min, z_max : float
            Redshift range
        n_points : int
            Number of grid points

        Returns
        -------
        tuple
            (z_grid, mu_grid)
        """
        cached = self.get(Omega_m, Omega_L, H0, z_min, z_max, n_points)
        if cached is not None:
            return cached

        # Compute new curve
        from ..models.cosmology import mu_theory

        z_grid = np.logspace(np.log10(z_min), np.log10(z_max), n_points)
        mu_grid = mu_theory(z_grid, Omega_m, Omega_L, H0)

        self.put(Omega_m, Omega_L, H0, z_min, z_max, n_points, z_grid, mu_grid)
        return z_grid, mu_grid

    def clear(self):
        """Clear the cache."""
        self._cache.clear()
        self._access_order.clear()
        self.stats = CacheStats()

    def __len__(self) -> int:
        return len(self._cache)


# Global cache instance
_cosmo_cache: Optional[CosmoCache] = None


def get_cosmo_cache(max_size: int = 32) -> CosmoCache:
    """Get or create global cosmology cache."""
    global _cosmo_cache
    if _cosmo_cache is None:
        _cosmo_cache = CosmoCache(max_size)
    return _cosmo_cache


def clear_all_caches():
    """Clear all performance caches."""
    global _cosmo_cache
    if _cosmo_cache is not None:
        _cosmo_cache.clear()

    # Also clear model caches
    from ..models.cosmology import clear_cache
    clear_cache()


class PlotOptimizer:
    """
    Optimization utilities for matplotlib plotting.
    """

    @staticmethod
    def should_use_fast_render(n_points: int, threshold: int = 1000) -> bool:
        """Determine if fast rendering should be used."""
        return n_points > threshold

    @staticmethod
    def get_marker_size(n_points: int) -> float:
        """Get appropriate marker size based on point count."""
        if n_points < 100:
            return 6.0
        elif n_points < 500:
            return 4.0
        elif n_points < 2000:
            return 2.5
        else:
            return 1.5

    @staticmethod
    def get_alpha(n_points: int) -> float:
        """Get appropriate alpha based on point count."""
        if n_points < 100:
            return 0.9
        elif n_points < 500:
            return 0.8
        elif n_points < 2000:
            return 0.6
        else:
            return 0.4
