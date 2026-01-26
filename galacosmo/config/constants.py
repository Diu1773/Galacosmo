"""Physical constants for GalaCosmo."""

# Gravitational constant in kpc * (km/s)^2 / Msun
G = 4.30091e-6

# Speed of light in km/s
C_KM_S = 299792.458

# Reference mass-to-light ratios for SPARC rotmod normalization (Upsilon=1)
ML_REF_DISK = 1.0
ML_REF_BULGE = 1.0

# Default cosmological parameters (Planck 2018)
DEFAULT_H0 = 67.4  # km/s/Mpc
DEFAULT_OMEGA_M = 0.315
DEFAULT_OMEGA_L = 0.685

# Cosmological parameter presets
COSMO_PRESETS = {
    "planck2018": {
        "name": "Planck 2018",
        "H0": 67.4,
        "Omega_m": 0.315,
        "Omega_L": 0.685,
    },
    "planck2015": {
        "name": "Planck 2015",
        "H0": 67.8,
        "Omega_m": 0.308,
        "Omega_L": 0.692,
    },
    "wmap9": {
        "name": "WMAP9",
        "H0": 69.3,
        "Omega_m": 0.287,
        "Omega_L": 0.713,
    },
    "riess2022": {
        "name": "Riess+ 2022 (SH0ES)",
        "H0": 73.0,
        "Omega_m": 0.315,
        "Omega_L": 0.685,
    },
}

# Halo model fitting bounds
HALO_BOUNDS = {
    "ISO": {
        "rho0": {"init": 1e7, "min": 1e5, "max": 1e10},  # M_sun/kpc^3
        "rc": {"init": 5.0, "min": 0.1, "max": 100.0},   # kpc
    },
    "NFW": {
        "V200": {"init": 120.0, "min": 30.0, "max": 400.0},  # km/s
        "c": {"init": 10.0, "min": 3.0, "max": 30.0},
    },
}
