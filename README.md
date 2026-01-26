# GalaCosmo

Galaxy rotation-curve and SN Ia Hubble-diagram analysis in a Qt desktop app.

## Features

- Rotation-curve fitting with ISO and NFW halos
- Baryonic component scaling (disk/bulge/gas) using SPARC conventions
- SN Ia Hubble diagram with residuals and comparison cosmology models
- Optional 3D galaxy visualization (PyVista)

## Quick start

```bash
# From source
python run_galacosmo.py
# or
python -m galacosmo
```

If installed as a package:

```bash
galacosmo
# or
galacosmo-gui
```

## Installation

```bash
pip install -e .
```

Dev tools:

```bash
pip install -e .[dev]
```

## Build (PyInstaller)

This builds the packaged app using the existing `GalaCosmo.spec`.

```bash
python build_exe.py --clean --noconfirm
```

Output goes to `dist/GalaCosmo/`.

Note: build on the target OS (Windows EXE requires a Windows build host).

## Data files

Place sample input data under `data/` (repo root):

- SPARC: `data/SPARC_Table1.txt`, `data/SPARC_Table2.txt`
- Union2.1 SN Ia: `data/SCPUnion2.1_AllSNe.tex`, `data/SCPUnion2.1_mu_vs_z.txt`

Load SPARC files in the Rotation Curve window. For SN Ia, use the Hubble Diagram
window and load `.txt`, `.csv`, `.dat`, or Union2.1 `.tex` files.

## SPARC input tables

### Table 1 (one row per galaxy; global parameters)

- Galaxy: name (e.g., CamB, D512-2)
- T: Hubble type code
- D, e_D: distance (Mpc) and mean error
- f_D: distance method flag (1=Hubble flow, 2=TRGB, 3=Cepheid, 4=Ursa Major, 5=SN, etc.)
- Inc, e_Inc: inclination and error (deg)
- L[3.6], e_L[3.6]: total 3.6um luminosity (typically 10^9 Lsun) and error
- Reff: effective radius at 3.6um (kpc)
- SBeff: effective surface brightness (Lsun/pc^2)
- Rdisk: disk scale length (kpc)
- SBdisk: disk central surface brightness (Lsun/pc^2)
- MHI: HI mass (typically 10^9 Msun)
- RHI: HI radius at 1 Msun/pc^2 (kpc)
- Vflat, e_Vflat: asymptotically flat rotation speed (km/s) and error
  - Values like 0.0 can mean Vflat is not defined for that galaxy in the table.
- Q: rotation curve quality flag (1=High, 2=Medium, 3=Low)
- Ref: source code for the rotation-curve data

### Table 2 (multiple rows per galaxy; radius-dependent curves)

- ID, D, R, Vobs, e_Vobs, Vgas, Vdisk, Vbul, SBdisk, SBbul
- Each row is a radius sample. Vobs is the observed rotation speed, and Vgas/Vdisk/Vbul are component contributions.
- SBdisk/SBbul are surface brightness profiles at 3.6um (Lsun/pc^2).

## M/L assumptions at 3.6um

In SPARC, Vdisk and Vbul in the Newtonian mass models are tabulated at Upsilon=1
(Msun/Lsun) to make rescaling easy. A common choice in the literature is a fixed
3.6um M/L with small scatter:

- Upsilon_3.6 (disk) ~= 0.5
- Upsilon_3.6 (bulge) ~= 0.7

### Scaling rules for SPARC rotmod velocities

SPARC component velocities are provided at Upsilon=1. To use a different M/L, scale velocities by sqrt(M/L):

- Vdisk(Upsilon_d) = sqrt(Upsilon_d) * Vdisk(Upsilon=1)
- Vbul(Upsilon_b) = sqrt(Upsilon_b) * Vbul(Upsilon=1)
- Gas does not use an M/L scaling.

Equivalently in quadrature:

- Vbar^2 = Vgas^2 + Upsilon_d * Vdisk^2 + Upsilon_b * Vbul^2

Example: if Upsilon_d=0.5, Vdisk scales by sqrt(0.5) ~= 0.707. If Upsilon_b=0.7, Vbul scales by sqrt(0.7) ~= 0.837.

Surface brightness to surface mass density is linear:

- Sigma_*(R) = Upsilon * SB(R)

## SN Ia Hubble data (Union2.1)

- The bundled sample file `data/SCPUnion2.1_mu_vs_z.txt` comes from the Supernova Cosmology Project (SCP) Union2.1 compilation hosted by Lawrence Berkeley National Laboratory (LBNL).
- The Hubble diagram expects columns like z, mu, and optionally emu (1-sigma uncertainty).
- For full Union2.1 metadata and literature matching, use `data/SCPUnion2.1_AllSNe.tex`.

### Union2.1 literature matching (AllSNe)

Union2.1 AllSNe rows include a sample ID in the **last column**, which encodes the
originating literature sample. The app maps that `sample_id` to a human-readable
paper label and uses it for coloring/labels in the Hubble diagram.

- Loader: `galacosmo/data/snia_loader.py` (`load_union21_latex`)
- Default mapping: `DEFAULT_SAMPLE_MAPPING` in the loader
- Optional mapping file: `galacosmo/config/union21_sample_mapping.json`

## UI quick start

- Rotation curve: Load Files (Table1 + Table2) -> Select Galaxy -> choose halo model and M/L -> compare Observed/Baryons/Total.
- Hubble diagram: Add Files or Add Folder -> set reference cosmology preset -> compare fixed models and residuals.

## Notes & troubleshooting

- The Rotation Curve window includes a "Galaxy 3D View" tab that visualizes the disk/bulge
  using Table2 surface-brightness profiles (SBdisk/SBbul). Gas is not included in the 3D view.
- Simple 3D logic:
  1) load Table2 profiles -> 2) scale by M/L -> 3) interpolate onto a 3D grid
  4) apply a vertical sech^2 profile -> 5) render with PyVista (optional spiral/halo overlays)
- The 3D galaxy tab requires `pyvista` + `pyvistaqt`. If they are missing, the viewer shows a message and remains disabled.
- If running from an installed package location that is read-only, the app falls back to a user-writable icon cache.

## In this codebase

- Reference M/L normalization is defined in `galacosmo/config/constants.py`:
  - `ML_REF_DISK = 1.0`
  - `ML_REF_BULGE = 1.0`
- Baryon scaling is implemented in `galacosmo/models/baryon.py` and follows the sqrt(M/L) rule above.
- Summary: Table2 uses Upsilon=1, and the UI M/L values rescale Vdisk/Vbul at runtime.
