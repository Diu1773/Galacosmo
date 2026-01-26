"""
Galaxy structure models for 3D visualization.

Literature references:
- Freeman (1970): Exponential disk model
- Sérsic (1968): Sérsic surface brightness profile
- van der Kruit & Searle (1981): Disk vertical structure (sech² law)
- Hernquist (1990): Spherical bulge approximation
- Navarro, Frenk & White (1996, 1997): NFW dark matter halo
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from scipy.special import gamma as gamma_func


@dataclass
class GalaxyParams:
    """Container for galaxy structural parameters."""
    # Disk parameters
    h_R: float = 3.0          # Disk scale length [kpc]
    h_z: float = 0.3          # Disk scale height [kpc] (typically h_R/10)
    Sigma0_disk: float = 1.0  # Central surface density [arbitrary]

    # Bulge parameters
    R_e: float = 1.0          # Effective radius [kpc]
    n_sersic: float = 2.0     # Sérsic index (n=1: exponential, n=4: de Vaucouleurs)
    Sigma0_bulge: float = 0.0 # Central surface density [arbitrary]

    # Halo parameters (for visualization only)
    r_s: float = 20.0         # NFW scale radius [kpc]
    rho_s: float = 1e6        # NFW scale density [M_sun/kpc^3]

    # Inclination for projection
    inclination: float = 60.0  # degrees


def sech2(x: np.ndarray) -> np.ndarray:
    """Hyperbolic secant squared function."""
    return 1.0 / np.cosh(x)**2


def b_n_sersic(n: float) -> float:
    """
    Compute b_n for Sérsic profile.

    Approximation from Ciotti & Bertin (1999):
    b_n ≈ 2n - 1/3 + 4/(405n) + 46/(25515n²)
    """
    if n <= 0:
        return 0.0
    return 2.0 * n - 1.0/3.0 + 4.0/(405.0*n) + 46.0/(25515.0*n**2)


class ExponentialDisk:
    """
    Exponential disk model following Freeman (1970).

    Surface brightness: Σ(R) = Σ₀ exp(-R/h_R)
    3D density: ρ(R,z) = (Σ₀/2h_z) exp(-R/h_R) sech²(z/h_z)

    The sech² vertical profile follows van der Kruit & Searle (1981).
    """

    def __init__(self, h_R: float, h_z: float, Sigma0: float = 1.0):
        """
        Initialize exponential disk.

        Parameters
        ----------
        h_R : float
            Radial scale length [kpc]
        h_z : float
            Vertical scale height [kpc]
        Sigma0 : float
            Central surface density [arbitrary units]
        """
        self.h_R = max(h_R, 0.1)
        self.h_z = max(h_z, 0.01)
        self.Sigma0 = Sigma0

    def surface_density(self, R: np.ndarray) -> np.ndarray:
        """
        Compute surface density at radius R.

        Σ(R) = Σ₀ exp(-R/h_R)
        """
        R = np.asarray(R, dtype=float)
        return self.Sigma0 * np.exp(-R / self.h_R)

    def density_3d(self, R: np.ndarray, z: np.ndarray) -> np.ndarray:
        """
        Compute 3D density at position (R, z).

        ρ(R,z) = (Σ₀/2h_z) exp(-R/h_R) sech²(z/h_z)
        """
        R = np.asarray(R, dtype=float)
        z = np.asarray(z, dtype=float)

        rho0 = self.Sigma0 / (2.0 * self.h_z)
        radial = np.exp(-R / self.h_R)
        vertical = sech2(z / self.h_z)

        return rho0 * radial * vertical


class SersicBulge:
    """
    Sérsic bulge model (Sérsic 1968).

    Surface brightness: Σ(R) = Σ_e exp(-b_n[(R/R_e)^(1/n) - 1])

    For 3D deprojection, we use the Hernquist (1990) approximation
    for computational efficiency.
    """

    def __init__(self, R_e: float, n: float = 2.0, Sigma0: float = 1.0):
        """
        Initialize Sérsic bulge.

        Parameters
        ----------
        R_e : float
            Effective (half-light) radius [kpc]
        n : float
            Sérsic index (n=1: exponential, n=4: de Vaucouleurs)
        Sigma0 : float
            Central surface density [arbitrary units]
        """
        self.R_e = max(R_e, 0.01)
        self.n = max(n, 0.5)
        self.b_n = b_n_sersic(self.n)
        self.Sigma0 = Sigma0

    def surface_density(self, R: np.ndarray) -> np.ndarray:
        """
        Compute surface density at radius R.

        Σ(R) = Σ₀ exp(-b_n[(R/R_e)^(1/n) - 1])
        """
        R = np.asarray(R, dtype=float)
        R_safe = np.maximum(R, 1e-6)
        exponent = self.b_n * ((R_safe / self.R_e)**(1.0/self.n) - 1.0)
        return self.Sigma0 * np.exp(-exponent)

    def density_3d(self, r: np.ndarray) -> np.ndarray:
        """
        Compute 3D density using Hernquist-like approximation.

        For n≈2-4, we use a deprojected Sérsic approximation:
        ρ(r) ∝ (r/R_e)^(-p) exp(-b_n (r/R_e)^(1/n))

        where p ≈ 1 - 0.6097/n + 0.05563/n² (Prugniel-Simien 1997)
        """
        r = np.asarray(r, dtype=float)
        r_safe = np.maximum(r, 1e-6)

        # Prugniel-Simien approximation for deprojection
        p = 1.0 - 0.6097/self.n + 0.05563/self.n**2

        x = r_safe / self.R_e
        rho = (x**(-p)) * np.exp(-self.b_n * x**(1.0/self.n))

        # Normalize to match central density
        rho *= self.Sigma0 / self.R_e

        return rho


class NFWHalo:
    """
    NFW dark matter halo (Navarro, Frenk & White 1996, 1997).

    Density: ρ(r) = ρ_s / [(r/r_s)(1 + r/r_s)²]
    """

    def __init__(self, r_s: float, rho_s: float):
        """
        Initialize NFW halo.

        Parameters
        ----------
        r_s : float
            Scale radius [kpc]
        rho_s : float
            Characteristic density [M_sun/kpc³]
        """
        self.r_s = max(r_s, 0.1)
        self.rho_s = rho_s

    def density_3d(self, r: np.ndarray) -> np.ndarray:
        """Compute 3D density at radius r."""
        r = np.asarray(r, dtype=float)
        r_safe = np.maximum(r, 1e-6)
        x = r_safe / self.r_s
        return self.rho_s / (x * (1.0 + x)**2)


class ISOHalo:
    """
    Isothermal sphere dark matter halo.

    Density: ρ(r) = ρ₀ / [1 + (r/r_c)²]
    """

    def __init__(self, r_c: float, rho_0: float):
        """
        Initialize isothermal halo.

        Parameters
        ----------
        r_c : float
            Core radius [kpc]
        rho_0 : float
            Central density [M_sun/kpc³]
        """
        self.r_c = max(r_c, 0.1)
        self.rho_0 = rho_0

    def density_3d(self, r: np.ndarray) -> np.ndarray:
        """Compute 3D density at radius r."""
        r = np.asarray(r, dtype=float)
        return self.rho_0 / (1.0 + (r / self.r_c)**2)


class GalaxyModel:
    """
    Complete galaxy model combining disk, bulge, and halo components.

    This class provides methods to generate 3D density grids suitable
    for PyVista visualization.
    """

    def __init__(
        self,
        disk: Optional[ExponentialDisk] = None,
        bulge: Optional[SersicBulge] = None,
        halo: Optional[NFWHalo] = None,
    ):
        """
        Initialize galaxy model.

        Parameters
        ----------
        disk : ExponentialDisk, optional
            Disk component
        bulge : SersicBulge, optional
            Bulge component
        halo : NFWHalo or ISOHalo, optional
            Dark matter halo component
        """
        self.disk = disk
        self.bulge = bulge
        self.halo = halo

    @classmethod
    def from_sparc_data(
        cls,
        R: np.ndarray,
        SBdisk: np.ndarray,
        SBbul: np.ndarray,
        ml_disk: float = 0.5,
        ml_bulge: float = 0.7,
        h_R: Optional[float] = None,
        R_e: Optional[float] = None,
        halo_params: Optional[Dict[str, float]] = None,
    ) -> "GalaxyModel":
        """
        Create galaxy model from SPARC data.

        Parameters
        ----------
        R : array
            Radius array from Table2 [kpc]
        SBdisk : array
            Disk surface brightness profile [L_sun/pc²]
        SBbul : array
            Bulge surface brightness profile [L_sun/pc²]
        ml_disk : float
            Disk mass-to-light ratio
        ml_bulge : float
            Bulge mass-to-light ratio
        h_R : float, optional
            Disk scale length. If None, estimated from data.
        R_e : float, optional
            Bulge effective radius. If None, estimated from data.
        halo_params : dict, optional
            Halo parameters {'model': 'NFW'/'ISO', 'p1': ..., 'p2': ...}

        Returns
        -------
        GalaxyModel
            Configured galaxy model
        """
        # Clean data
        R = np.asarray(R, dtype=float)
        SBdisk = np.nan_to_num(SBdisk, nan=0.0)
        SBbul = np.nan_to_num(SBbul, nan=0.0)

        # Apply M/L scaling (SB → surface mass density)
        Sigma_disk = SBdisk * ml_disk
        Sigma_bulge = SBbul * ml_bulge

        # Estimate disk scale length if not provided
        if h_R is None:
            # Fit exponential to log(SB) vs R
            valid = (R > 0) & (Sigma_disk > 0)
            if np.any(valid):
                # Simple estimate: h_R ≈ R where SB drops to 1/e
                peak = np.nanmax(Sigma_disk)
                target = peak / np.e
                idx = np.where(Sigma_disk[valid] <= target)[0]
                if len(idx) > 0:
                    h_R = R[valid][idx[0]]
                else:
                    h_R = np.nanmax(R) / 3.0
            else:
                h_R = 3.0

        # Estimate bulge effective radius if not provided
        if R_e is None:
            valid = (R > 0) & (Sigma_bulge > 0)
            if np.any(valid):
                # Half-light radius estimate
                cumsum = np.cumsum(Sigma_bulge[valid] * R[valid])
                total = cumsum[-1] if cumsum[-1] > 0 else 1.0
                half_idx = np.searchsorted(cumsum, total / 2)
                R_e = R[valid][min(half_idx, len(R[valid])-1)]
            else:
                R_e = 1.0

        # Create components
        disk = ExponentialDisk(
            h_R=h_R,
            h_z=h_R / 10.0,  # Standard ratio
            Sigma0=np.nanmax(Sigma_disk) if np.any(Sigma_disk > 0) else 0.0
        )

        bulge = SersicBulge(
            R_e=R_e,
            n=2.0,  # Typical for disk galaxy bulges
            Sigma0=np.nanmax(Sigma_bulge) if np.any(Sigma_bulge > 0) else 0.0
        )

        # Create halo if parameters provided
        halo = None
        if halo_params:
            model = halo_params.get('model', 'NFW').upper()
            if model == 'NFW':
                V200 = halo_params.get('p1', 150.0)
                c = halo_params.get('p2', 10.0)
                # Convert V200, c to r_s, rho_s
                # R200 = V200 / (10 * H0_kpc) where H0_kpc = H0/1000
                H0 = halo_params.get('H0', 67.4)
                R200 = V200 / (10.0 * H0 / 1000.0)
                r_s = R200 / c
                # rho_s from NFW mass formula
                rho_s = 200 * (H0/1000.0)**2 * c**3 / (3 * (np.log(1+c) - c/(1+c)))
                halo = NFWHalo(r_s=r_s, rho_s=rho_s)
            else:  # ISO
                rho0 = halo_params.get('p1', 1e7)
                rc = halo_params.get('p2', 5.0)
                halo = ISOHalo(r_c=rc, rho_0=rho0)

        return cls(disk=disk, bulge=bulge, halo=halo)

    def compute_density_grid(
        self,
        r_max: float,
        n_xy: int = 100,
        n_z: int = 30,
        components: str = "all",
        include_halo: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute 3D density grid for visualization.

        Parameters
        ----------
        r_max : float
            Maximum radius [kpc]
        n_xy : int
            Number of grid points in x and y
        n_z : int
            Number of grid points in z
        components : str
            Which components: "disk", "bulge", "all"
        include_halo : bool
            Whether to include dark matter halo

        Returns
        -------
        tuple
            (X, Y, Z, density) arrays
        """
        # Create grid
        xy = np.linspace(-r_max, r_max, n_xy)
        z_max = r_max / 3.0  # Disk is thin
        z = np.linspace(-z_max, z_max, n_z)

        X, Y, Z = np.meshgrid(xy, xy, z, indexing='ij')
        R_cyl = np.sqrt(X**2 + Y**2)  # Cylindrical radius
        r_sph = np.sqrt(X**2 + Y**2 + Z**2)  # Spherical radius

        density = np.zeros_like(X)

        # Add disk component
        if self.disk and components in ("disk", "all"):
            density += self.disk.density_3d(R_cyl, Z)

        # Add bulge component
        if self.bulge and components in ("bulge", "all"):
            density += self.bulge.density_3d(r_sph)

        # Add halo (optional, usually shown separately)
        if include_halo and self.halo:
            # Scale halo for visibility (much lower density)
            halo_density = self.halo.density_3d(r_sph)
            halo_density = halo_density / np.nanmax(halo_density) * np.nanmax(density) * 0.1
            density += halo_density

        return X, Y, Z, density

    def compute_density_from_profile(
        self,
        R: np.ndarray,
        profile: np.ndarray,
        r_max: float,
        n_xy: int = 100,
        n_z: int = 30,
        h_z: Optional[float] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute 3D density grid directly from observed radial profile.

        This method uses the actual SPARC SB profile data instead of
        fitted parametric models.

        Parameters
        ----------
        R : array
            Radius array [kpc]
        profile : array
            Surface brightness/density profile
        r_max : float
            Maximum radius for grid [kpc]
        n_xy : int
            Grid resolution in xy plane
        n_z : int
            Grid resolution in z direction
        h_z : float, optional
            Scale height [kpc]. If None, uses r_max/20.

        Returns
        -------
        tuple
            (X, Y, Z, density) arrays
        """
        if h_z is None:
            h_z = r_max / 20.0

        # Create grid
        xy = np.linspace(-r_max, r_max, n_xy)
        z_max = r_max / 4.0
        z_arr = np.linspace(-z_max, z_max, n_z)

        X, Y, Z = np.meshgrid(xy, xy, z_arr, indexing='ij')
        R_cyl = np.sqrt(X**2 + Y**2)

        # Sort data for interpolation
        sort_idx = np.argsort(R)
        R_sorted = R[sort_idx]
        profile_sorted = np.nan_to_num(profile[sort_idx], nan=0.0)

        # Interpolate profile onto grid
        Sigma_grid = np.interp(
            R_cyl.ravel(),
            R_sorted,
            profile_sorted,
            left=profile_sorted[0] if len(profile_sorted) > 0 else 0.0,
            right=0.0
        ).reshape(R_cyl.shape)

        # Apply vertical structure (sech² law)
        vertical = sech2(Z / h_z)
        density = (Sigma_grid / (2.0 * h_z)) * vertical

        return X, Y, Z, density


def create_spiral_arm_pattern(
    X: np.ndarray,
    Y: np.ndarray,
    n_arms: int = 2,
    pitch_angle: float = 15.0,
    arm_width: float = 0.3,
) -> np.ndarray:
    """
    Create spiral arm modulation pattern.

    Parameters
    ----------
    X, Y : array
        Coordinate grids
    n_arms : int
        Number of spiral arms
    pitch_angle : float
        Pitch angle in degrees
    arm_width : float
        Relative width of arms (0-1)

    Returns
    -------
    array
        Modulation factor (1 = arm, 0 = inter-arm)
    """
    R = np.sqrt(X**2 + Y**2)
    theta = np.arctan2(Y, X)

    # Logarithmic spiral: θ = (1/tan(pitch)) * ln(r/a)
    pitch_rad = np.deg2rad(pitch_angle)
    k = 1.0 / np.tan(pitch_rad)

    # Spiral phase
    R_safe = np.maximum(R, 1e-6)
    spiral_phase = theta - k * np.log(R_safe)

    # Modulation (cosine with n_arms)
    modulation = 0.5 * (1.0 + np.cos(n_arms * spiral_phase))

    # Smooth the arms
    modulation = arm_width + (1.0 - arm_width) * modulation

    return modulation
