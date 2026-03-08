# GalaCosmo

## 한국어 안내

`GalaCosmo`는 예비교사가 공개 천문 데이터(OER)를 바탕으로 암흑물질과 우주론을 직관적으로 탐구할 수 있도록 만든 GUI 프로그램입니다. 핵심 활동은 SPARC 은하 회전곡선 데이터를 이용해 가시물질과 암흑물질 헤일로의 기여를 비교하는 것이며, 코딩 없이 클릭과 슬라이더 조작만으로 분석할 수 있습니다.

### 프로그램 개요

- SPARC 실제 관측 데이터를 불러와 은하 회전곡선을 비교합니다.
- `disk`, `bulge`, `gas` 성분과 `ISO`, `NFW` 헤일로 모델을 조절하며 암흑물질의 필요성을 탐구합니다.
- PyVista 기반 3D 보기로 은하 원반, 벌지, 헤일로 구조를 공간적으로 이해할 수 있습니다.
- SN Ia 허블 다이어그램 기능은 데이터 리터러시와 우주론 확장 활동에 활용할 수 있습니다.

### 예비교사용 활용 포인트

- 코딩보다 해석에 집중: 계산 과정 대신 그래프와 시각화 결과의 의미를 토론할 수 있습니다.
- 실제 데이터 기반 탐구: 연구 데이터와 교육 활동을 직접 연결할 수 있습니다.
- 모델 비교 중심 수업: `M/L` 변화, `ISO` 대 `NFW`, 잔차 비교를 통해 모델 선택의 근거를 논의할 수 있습니다.
- 수업 설계 확장성: 암흑물질, 은하 구조, 데이터 리터러시, 현대 우주론 단원을 연결할 수 있습니다.

### 빠른 실행

```bash
python run_galacosmo.py
# 또는
python -m galacosmo
```

패키지 설치 후에는 다음 명령도 사용할 수 있습니다.

```bash
galacosmo
# 또는
galacosmo-gui
```

### 설치

```bash
pip install -e .
```

개발 도구까지 설치하려면:

```bash
pip install -e .[dev]
```

### 데이터 파일

루트의 `data/` 폴더에 예시 입력 데이터가 포함되어 있습니다.

- SPARC: `data/SPARC_Table1.txt`, `data/SPARC_Table2.txt`
- Union2.1 SN Ia: `data/SCPUnion2.1_mu_vs_z.txt`

회전곡선 탐구는 `Rotation Curve` 창에서 SPARC 파일을 불러와 사용합니다. 허블 다이어그램은 `.txt`, `.csv`, `.dat`, `Union2.1 .tex` 파일을 지원합니다.

### 권장 탐구 흐름

1. `Table1`, `Table2`를 불러오고 은하 하나를 선택합니다.
2. `Observed`와 `Baryons`를 먼저 비교해 가시물질만으로 외곽부 회전속도를 설명할 수 있는지 봅니다.
3. `M/L Disk`, `M/L Bulge` 값을 조절하며 별빛-질량 변환 가정이 결과에 어떤 영향을 주는지 확인합니다.
4. `ISO`와 `NFW` 헤일로 모델을 번갈아 적용하고 `Total` 및 `Residuals`를 비교합니다.
5. `Galaxy 3D View`에서 질량 분포를 입체적으로 확인하고 2D 그래프 해석과 연결합니다.

### 해석 시 유의사항

- SPARC의 `Vdisk`, `Vbul`은 `Upsilon = 1` 기준으로 제공되며, 앱에서 사용자가 입력한 `M/L` 값으로 재스케일됩니다.
- `Baryons = sqrt(Disk^2 + Bulge^2 + Gas^2)`
- `Total = sqrt(Baryons^2 + Halo^2)`
- 3D 보기의 목적은 공간적 직관 제공이며, 가스 분포 등 일부 성분은 단순화되어 표현됩니다.
- 교육적 탐구용 기본값이 포함되어 있으므로, 연구 보고서나 논문화에는 원문 데이터 정의와 문헌 값을 함께 확인하는 것이 좋습니다.

### 참고 문헌 및 데이터 출처

- SPARC database: Lelli, McGaugh, Schombert (2016), AJ 152, 157.
- NFW halo: Navarro, Frenk, White (1996, 1997).
- Pseudo-isothermal halo: Begeman et al. (1991).
- SN Ia Union2.1: Suzuki et al. (2012), ApJ 746, 85.
- Cosmology distance reference: Hogg (1999), *Distance measures in cosmology*.

## English Reference

Galaxy rotation-curve and SN Ia Hubble-diagram analysis in a Qt desktop app.

### Features

- Rotation-curve fitting with ISO and NFW halos
- Baryonic component scaling (disk/bulge/gas) using SPARC conventions
- SN Ia Hubble diagram with residuals and comparison cosmology models
- Optional 3D galaxy visualization (PyVista)

### Quick start

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

### Installation

```bash
pip install -e .
```

Dev tools:

```bash
pip install -e .[dev]
```

### Build (PyInstaller)

This builds the packaged app using the existing `GalaCosmo.spec`.

```bash
python build_exe.py --clean --noconfirm
```

Output goes to `dist/GalaCosmo/`.

Note: build on the target OS (Windows EXE requires a Windows build host).

### Data files

Place sample input data under `data/` (repo root):

- SPARC: `data/SPARC_Table1.txt`, `data/SPARC_Table2.txt`
- Union2.1 SN Ia: `data/SCPUnion2.1_AllSNe.tex`, `data/SCPUnion2.1_mu_vs_z.txt`

Load SPARC files in the Rotation Curve window. For SN Ia, use the Hubble Diagram
window and load `.txt`, `.csv`, `.dat`, or Union2.1 `.tex` files.

### SPARC input tables

#### Table 1 (one row per galaxy; global parameters)

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

#### Table 2 (multiple rows per galaxy; radius-dependent curves)

- ID, D, R, Vobs, e_Vobs, Vgas, Vdisk, Vbul, SBdisk, SBbul
- Each row is a radius sample. Vobs is the observed rotation speed, and Vgas/Vdisk/Vbul are component contributions.
- SBdisk/SBbul are surface brightness profiles at 3.6um (Lsun/pc^2).

### M/L assumptions at 3.6um

In SPARC, Vdisk and Vbul in the Newtonian mass models are tabulated at Upsilon=1
(Msun/Lsun) to make rescaling easy. A common choice in the literature is a fixed
3.6um M/L with small scatter:

- Upsilon_3.6 (disk) ~= 0.5
- Upsilon_3.6 (bulge) ~= 0.7

#### Scaling rules for SPARC rotmod velocities

SPARC component velocities are provided at Upsilon=1. To use a different M/L, scale velocities by sqrt(M/L):

- Vdisk(Upsilon_d) = sqrt(Upsilon_d) * Vdisk(Upsilon=1)
- Vbul(Upsilon_b) = sqrt(Upsilon_b) * Vbul(Upsilon=1)
- Gas does not use an M/L scaling.

Equivalently in quadrature:

- Vbar^2 = Vgas^2 + Upsilon_d * Vdisk^2 + Upsilon_b * Vbul^2

Example: if Upsilon_d=0.5, Vdisk scales by sqrt(0.5) ~= 0.707. If Upsilon_b=0.7, Vbul scales by sqrt(0.7) ~= 0.837.

Surface brightness to surface mass density is linear:

- Sigma_*(R) = Upsilon * SB(R)

### SN Ia Hubble data (Union2.1)

- The bundled sample file `data/SCPUnion2.1_mu_vs_z.txt` comes from the Supernova Cosmology Project (SCP) Union2.1 compilation hosted by Lawrence Berkeley National Laboratory (LBNL).
- The Hubble diagram expects columns like z, mu, and optionally emu (1-sigma uncertainty).
- For full Union2.1 metadata and literature matching, use `data/SCPUnion2.1_AllSNe.tex`.

#### Union2.1 literature matching (AllSNe)

Union2.1 AllSNe rows include a sample ID in the **last column**, which encodes the
originating literature sample. The app maps that `sample_id` to a human-readable
paper label and uses it for coloring/labels in the Hubble diagram.

- Loader: `galacosmo/data/snia_loader.py` (`load_union21_latex`)
- Default mapping: `DEFAULT_SAMPLE_MAPPING` in the loader
- Optional mapping file: `galacosmo/config/union21_sample_mapping.json`

### UI quick start

- Rotation curve: Load Files (Table1 + Table2) -> Select Galaxy -> choose halo model and M/L -> compare Observed/Baryons/Total.
- Hubble diagram: Add Files or Add Folder -> set reference cosmology preset -> compare fixed models and residuals.

### Notes & troubleshooting

- The Rotation Curve window includes a `Galaxy 3D View` tab that visualizes the disk/bulge using Table2 surface-brightness profiles (`SBdisk`/`SBbul`). Gas is not included in the 3D view.
- Simple 3D logic:
  1. load Table2 profiles
  2. scale by M/L
  3. interpolate onto a 3D grid
  4. apply a vertical `sech^2` profile
  5. render with PyVista (optional spiral/halo overlays)
- The 3D galaxy tab requires `pyvista` + `pyvistaqt`. If they are missing, the viewer shows a message and remains disabled.
- If running from an installed package location that is read-only, the app falls back to a user-writable icon cache.

### In this codebase

- Reference M/L normalization is defined in `galacosmo/config/constants.py`:
  - `ML_REF_DISK = 1.0`
  - `ML_REF_BULGE = 1.0`
- Baryon scaling is implemented in `galacosmo/models/baryon.py` and follows the `sqrt(M/L)` rule above.
- Summary: Table2 uses `Upsilon=1`, and the UI M/L values rescale `Vdisk` and `Vbul` at runtime.
