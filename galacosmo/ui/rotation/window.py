"""Rotation curve analysis window."""

import os
import re
import numpy as np
import pandas as pd

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFileDialog, QMessageBox, QSplitter, QTabWidget, QLabel, QPushButton,
    QScrollArea,
)
from ...config import get_settings
from ...config.palettes import ROTATION_COLORS
from ...config.constants import C_KM_S, ML_REF_DISK, ML_REF_BULGE
from ...data import read_table1, read_table2, find_sparc_files, get_default_data_dir
from ...models import compute_rotation_curves
from ..widgets import PlotCanvas, DualPanelCanvas
from ..galaxy3d import Galaxy3DViewer, Galaxy3DControlPanel
from .galaxy_picker import GalaxyPicker
from .controls import RotationControlPanel

try:
    import mplcursors
    HAS_MPLCURSORS = True
except ImportError:
    HAS_MPLCURSORS = False


class RotationCurveWindow(QMainWindow):
    """Window for galaxy rotation curve analysis."""

    def __init__(self, parent=None, app_icon=None):
        super().__init__(parent)
        self.settings = get_settings()
        self.app_icon = app_icon

        # Data state
        self.base_dir = ""
        self.table1_path = None
        self.table2_path = None
        self.table1_df = None
        self.table2_df = None
        self.current_galaxy = None
        self.current_data = None
        self.curves = None
        self._table2_galaxy_cache = {}
        self._table1_lookup = {}
        self._component_presence = {}
        self._show_residuals = True
        self._galaxy_view_dirty = True

        # For mplcursors interaction
        self._scatter_artist = None
        self._cursor = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.setWindowTitle("Rotation Curve Simulator")
        self.resize(1200, 750)

        if self.app_icon:
            self.setWindowIcon(self.app_icon)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # Splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Left: Plot tabs
        self.tabs = QTabWidget()

        self.canvas = DualPanelCanvas(figsize=(8, 6), height_ratios=(3, 1))
        self.canvas.set_help_text(
            "Rotation Curve Help\n\n"
            "- Observed + Total toggles data points and total curve\n"
            "- Right-click a curve checkbox to set its color\n"
            "- Baryons = sqrt(Disk^2 + Bulge^2 + Gas^2)\n"
            "- Baryons: combined mass from disk+bulge+gas (visible matter)\n"
            "- Total = sqrt(Baryons^2 + Halo^2)\n"
            "- Residuals show ΔV relative to the fitted total curve\n"
            "- Cosmology: H0/Omega_m/Omega_L apply to NFW/H(z) only\n"
            "- ISO: core-like halo (rho0, rc), no cosmology inputs\n"
            "- NFW: cuspy halo (V200, c), uses H0 and Omega parameters\n"
            "- rho0: ISO central density (M_sun/kpc^3)\n"
            "- rc: ISO core radius (kpc)\n"
            "- V200: NFW circular speed at R200 (km/s)\n"
            "- c: NFW concentration (dimensionless)\n"
        )
        self.rotation_tab = QWidget()
        rotation_layout = QVBoxLayout(self.rotation_tab)
        rotation_layout.setContentsMargins(0, 0, 0, 0)
        rotation_layout.setSpacing(6)
        rotation_layout.addWidget(self.canvas)

        residual_layout = QHBoxLayout()
        self.btn_residuals_toggle = QPushButton("Residuals: On")
        self.btn_residuals_toggle.setCheckable(True)
        self.btn_residuals_toggle.setChecked(True)
        residual_layout.addWidget(self.btn_residuals_toggle)
        residual_layout.addStretch()
        rotation_layout.addLayout(residual_layout)

        self.tabs.addTab(self.rotation_tab, "Rotation Curve")

        self.galaxy_view_widget = QWidget()
        galaxy_layout = QVBoxLayout(self.galaxy_view_widget)
        galaxy_layout.setContentsMargins(8, 8, 8, 8)
        galaxy_layout.setSpacing(6)

        # Header with galaxy name and select button
        galaxy_header = QHBoxLayout()
        self.lbl_galaxy_tab = QLabel("Galaxy: —")
        self.lbl_galaxy_tab.setObjectName("subtitle")
        galaxy_header.addWidget(self.lbl_galaxy_tab)
        galaxy_header.addStretch()
        self.btn_pick_galaxy_tab = QPushButton("Select Galaxy")
        galaxy_header.addWidget(self.btn_pick_galaxy_tab)
        galaxy_layout.addLayout(galaxy_header)

        # 3D Galaxy Viewer (PyVista-based)
        theme = self.settings.theme if hasattr(self.settings, 'theme') else "dark"
        self.galaxy_3d_viewer = Galaxy3DViewer(theme=theme)
        galaxy_layout.addWidget(self.galaxy_3d_viewer)

        self.tabs.addTab(self.galaxy_view_widget, "Galaxy 3D View")

        splitter.addWidget(self.tabs)

        # Right: Controls (wrapped in scroll areas for vertical resizing)
        self.controls_tabs = QTabWidget()
        self.rotation_controls = RotationControlPanel()
        self.galaxy_3d_controls = Galaxy3DControlPanel()

        rotation_scroll = QScrollArea()
        rotation_scroll.setWidget(self.rotation_controls)
        rotation_scroll.setWidgetResizable(True)
        rotation_scroll.setFrameShape(QScrollArea.NoFrame)

        galaxy3d_scroll = QScrollArea()
        galaxy3d_scroll.setWidget(self.galaxy_3d_controls)
        galaxy3d_scroll.setWidgetResizable(True)
        galaxy3d_scroll.setFrameShape(QScrollArea.NoFrame)

        self.controls_tabs.addTab(rotation_scroll, "Rotation Controls")
        self.controls_tabs.addTab(galaxy3d_scroll, "Galaxy 3D Controls")
        splitter.addWidget(self.controls_tabs)

        # Set initial sizes (70% plot, 30% controls)
        splitter.setSizes([700, 300])

    def _connect_signals(self):
        """Connect control panel signals."""
        self.rotation_controls.load_data_requested.connect(self._on_load_data)
        self.rotation_controls.pick_galaxy_requested.connect(self._on_pick_galaxy)
        self.rotation_controls.delete_files_requested.connect(self._on_delete_files)
        self.rotation_controls.clear_files_requested.connect(self._on_clear_files)
        self.rotation_controls.halo_model_changed.connect(self._on_halo_changed)
        self.rotation_controls.ml_changed.connect(self._on_ml_changed)
        self.rotation_controls.cosmology_changed.connect(self._run_fit)
        self.rotation_controls.rotation_settings_changed.connect(self._run_fit)
        self.rotation_controls.curve_style_changed.connect(self._update_plot)
        self.rotation_controls.curves_visibility_changed.connect(self._update_plot)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.controls_tabs.currentChanged.connect(self._on_controls_tab_changed)
        self.btn_residuals_toggle.toggled.connect(self._on_residuals_toggled)
        self.btn_pick_galaxy_tab.clicked.connect(self._on_pick_galaxy)

        # 3D Galaxy viewer controls
        self.galaxy_3d_controls.options_changed.connect(self._on_galaxy_3d_options_changed)
        self.galaxy_3d_controls.view_preset_requested.connect(self._on_galaxy_3d_view_preset)
        self.galaxy_3d_controls.screenshot_requested.connect(self._on_galaxy_3d_screenshot)

    def _on_load_data(self):
        """Handle load data request."""
        default_dir = get_default_data_dir()
        start_dir = self.base_dir or (str(default_dir) if default_dir else os.getcwd())
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select SPARC Table1 and Table2 Files",
            start_dir,
            "SPARC Files (*.mrt *.txt *.dat);;All Files (*)",
        )

        if not paths:
            return

        table1_path = None
        table2_path = None
        for path in paths:
            name = os.path.basename(path).lower()
            if "table1" in name:
                table1_path = path
            elif "table2" in name or ("mass" in name and "model" in name):
                table2_path = path

        if table1_path is None or table2_path is None:
            fallback_dir = os.path.dirname(paths[0])
            found_t1, found_t2 = find_sparc_files(fallback_dir)
            table1_path = table1_path or found_t1
            table2_path = table2_path or found_t2

        if not table1_path or not table2_path:
            QMessageBox.warning(
                self,
                "Files Not Found",
                "Please select both Table1 and Table2 files."
            )
            return

        self.base_dir = os.path.dirname(table1_path)
        self.table1_path = table1_path
        self.table2_path = table2_path
        self.rotation_controls.set_loaded_files([
            (f"Table1: {os.path.basename(table1_path)}", table1_path),
            (f"Table2: {os.path.basename(table2_path)}", table2_path),
        ])

        try:
            self.table1_df = read_table1(table1_path)
            self.table2_df = read_table2(table2_path)
            self._table2_galaxy_cache.clear()

            if "ID" in self.table2_df.columns and "ID_key" not in self.table2_df.columns:
                self.table2_df["ID_key"] = self.table2_df["ID"].astype(str).str.strip().str.lower()

            self._build_table1_lookup()
            self._build_component_presence()

            # Auto-select first galaxy
            if len(self.table1_df) > 0:
                self._set_galaxy(self.table1_df["Galaxy"].iloc[0])
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to read Table1:\n{e}"
                )

    def _on_pick_galaxy(self):
        """Handle pick galaxy request."""
        if self.table1_df is None:
            QMessageBox.information(
                self,
                "No Data",
                "Please load a data folder first."
            )
            return

        dialog = GalaxyPicker(self.table1_df, self._get_component_presence(), self)
        dialog.galaxy_selected.connect(self._set_galaxy)
        dialog.exec_()

    def _on_delete_files(self):
        """Delete selected files from the list."""
        selected = self.rotation_controls.get_selected_files()
        if not selected:
            QMessageBox.information(self, "No Selection", "Select a file to remove.")
            return
        self._clear_loaded_data()

    def _on_clear_files(self):
        """Clear all loaded files."""
        if not self.table1_path and not self.table2_path:
            return
        self._clear_loaded_data()

    def _clear_loaded_data(self):
        """Reset loaded data and UI."""
        self.table1_path = None
        self.table2_path = None
        self.table1_df = None
        self.table2_df = None
        self.current_galaxy = None
        self.current_data = None
        self.curves = None
        self._table2_galaxy_cache.clear()
        self._table1_lookup.clear()
        self._component_presence = {}
        self._galaxy_view_dirty = True
        self.rotation_controls.clear_loaded_files()
        self.rotation_controls.set_galaxy_name("")
        self.lbl_galaxy_tab.setText("Galaxy: —")
        self.canvas.clear()
        self.canvas.draw()
        self.galaxy_3d_viewer.clear()

    @staticmethod
    def _normalize_galaxy_name(name: str) -> str:
        """Normalize galaxy names for stable dictionary lookups."""
        return str(name).strip().lower()

    def _build_table1_lookup(self):
        """Precompute Table1 lookups used during fitting and 3D rendering."""
        self._table1_lookup = {}
        if self.table1_df is None or "Galaxy" not in self.table1_df.columns:
            return

        for _, row in self.table1_df.iterrows():
            key = self._normalize_galaxy_name(row["Galaxy"])
            self._table1_lookup[key] = {
                "D": row.get("D"),
                "Rdisk": row.get("Rdisk"),
            }

    def _build_component_presence(self):
        """Precompute per-galaxy component availability from Table2."""
        self._component_presence = {}
        if self.table2_df is None or "ID" not in self.table2_df.columns:
            return

        status_cols = ["Vgas", "Vdisk", "Vbul", "SBdisk", "SBbul"]
        grouped = self.table2_df.groupby("ID_key" if "ID_key" in self.table2_df.columns else "ID")

        for key, group in grouped:
            entry = {}
            for col in status_cols:
                if col not in group.columns:
                    entry[col] = False
                    continue
                values = pd.to_numeric(group[col], errors="coerce").fillna(0.0).to_numpy()
                entry[col] = bool((values != 0).any())
            self._component_presence[str(key).strip().lower()] = entry

    def _get_galaxy_table2_data(self, galaxy_name: str) -> pd.DataFrame:
        """Get Table2 rows for a galaxy using in-memory cache."""
        if self.table2_df is None:
            raise ValueError("Table2 data is not loaded")

        key = self._normalize_galaxy_name(galaxy_name)
        cached = self._table2_galaxy_cache.get(key)
        if cached is not None:
            return cached

        if "ID_key" in self.table2_df.columns:
            mask = self.table2_df["ID_key"] == key
        else:
            mask = self.table2_df["ID"].astype(str).str.strip().str.lower() == key

        if not mask.any():
            mask = self.table2_df["ID"].astype(str).str.contains(
                re.escape(galaxy_name), case=False, na=False
            )

        if not mask.any():
            raise ValueError(f"Galaxy '{galaxy_name}' not found in Table2")

        galaxy_df = self.table2_df.loc[mask].sort_values("R").reset_index(drop=True).copy()
        self._table2_galaxy_cache[key] = galaxy_df
        return galaxy_df

    def _get_component_presence(self) -> dict:
        """Build per-galaxy component presence map from Table2."""
        return self._component_presence

    def _set_galaxy(self, name: str):
        """Set current galaxy and run fit."""
        self.current_galaxy = name
        self.rotation_controls.set_galaxy_name(name)
        self.lbl_galaxy_tab.setText(f"Galaxy: {name}")
        self._run_fit()

    def _on_halo_changed(self, model: str):
        """Handle halo model change."""
        self._run_fit()

    def _on_ml_changed(self, ml_disk: float, ml_bulge: float):
        """Handle M/L change."""
        self._run_fit()

    def _on_residuals_toggled(self):
        """Handle residual panel toggle."""
        self._show_residuals = self.btn_residuals_toggle.isChecked()
        if self._show_residuals:
            self.btn_residuals_toggle.setText("Residuals: On")
        else:
            self.btn_residuals_toggle.setText("Residuals: Off")
        self._update_plot()

    def _run_fit(self):
        """Run rotation curve fitting."""
        if self.table2_df is None or not self.current_galaxy:
            return

        try:
            # Reuse cached, preloaded Table2 data by galaxy.
            data = self._get_galaxy_table2_data(self.current_galaxy)
            self.current_data = data
            self._galaxy_view_dirty = True

            R = data["R"].to_numpy(float)
            Vobs = data["Vobs"].to_numpy(float)
            eV = data["e_Vobs"].to_numpy(float)
            Vgas = data["Vgas"].to_numpy(float)
            Vdisk = data["Vdisk"].to_numpy(float)
            Vbul = data["Vbul"].to_numpy(float)

            ml_disk, ml_bulge = self.rotation_controls.get_ml_values()
            halo_model = self.rotation_controls.get_halo_model()
            halo_kwargs = self.rotation_controls.get_cosmology_params()

            z_est = 0.0
            table1_entry = self._table1_lookup.get(self._normalize_galaxy_name(self.current_galaxy))
            if table1_entry is not None:
                dist = table1_entry.get("D")
                try:
                    dist = float(dist)
                except (TypeError, ValueError):
                    dist = 0.0
                if np.isfinite(dist) and dist > 0:
                    z_est = (halo_kwargs["H0"] * dist) / C_KM_S
            halo_kwargs["z"] = z_est

            # Compute all curves
            self.curves = compute_rotation_curves(
                R, Vobs, eV, Vdisk, Vbul, Vgas,
                ml_disk, ml_bulge, halo_model,
                **halo_kwargs
            )

            # Update results display
            p1, p2 = self.curves["params"]
            self.rotation_controls.set_fit_results(halo_model, p1, p2)

            # Update plot
            self._update_plot()
            if self.tabs.currentWidget() == self.galaxy_view_widget:
                self._update_galaxy_3d_view()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Fit Error",
                f"Fitting failed:\n{e}"
            )

    def _update_plot(self, visibility=None):
        """Update the plot with current curves and visibility settings."""
        ax_main = self.canvas.ax_main
        ax_res = self.canvas.ax_residual
        ax_main.set_xscale("linear")
        ax_res.set_xscale("linear")
        ax_main.clear()
        ax_res.clear()
        self.canvas.set_residuals_visible(self._show_residuals)

        if self.curves is None:
            self.rotation_controls.update_chi2(None, None, 0)
            self.canvas.draw()
            return

        if visibility is None:
            visibility = self.rotation_controls.get_visibility()

        show_residuals = self._show_residuals

        R = self.curves["R"]
        Vobs = self.curves["Vobs"]
        eV = self.curves["eV"]
        r = self.curves["r"]

        # Reset scatter for mplcursors
        self._scatter_artist = None

        # Plot observed data
        if visibility.get("Observed", False):
            ax_main.errorbar(
                R, Vobs,
                yerr=np.nan_to_num(eV, nan=0.0),
                fmt="o", ms=4, capsize=2,
                elinewidth=0.6, alpha=0.85,
                color=ROTATION_COLORS["Observed"],
                label="Observed",
                zorder=5
            )
            # Add invisible scatter for mplcursors picking
            self._scatter_artist = ax_main.scatter(
                R, Vobs, s=40, alpha=0.0, picker=True
            )

        # Plot components
        components = [
            ("Disk", self.curves["Vd"], "--", 0.9),
            ("Bulge", self.curves["Vb"], "--", 0.9),
            ("Gas", self.curves["Vg"], "--", 0.9),
            ("Baryons", self.curves["Vbar"], "-", 1.4),
            ("Halo", self.curves["Vh"], "-", 1.2),
            ("Total", self.curves["Vtot"], "-", 2.0),
        ]

        for name, curve, ls, lw in components:
            if visibility.get(name, False):
                # Skip bulge if all zeros
                if name == "Bulge" and np.nanmax(curve) <= 0:
                    continue

                label = name
                if name == "Halo":
                    model = self.rotation_controls.get_halo_model()
                    label = f"Halo ({model})"

                ax_main.plot(
                    r, curve,
                    linestyle=ls, linewidth=lw,
                    color=ROTATION_COLORS[name],
                    label=label,
                    zorder=3 if name != "Total" else 4
                )

        # Styling
        ax_main.set_ylabel("Rotation Speed V [km/s]")
        ax_main.set_title(f"{self.current_galaxy} — Rotation Curve")
        ax_main.grid(True, alpha=0.25)
        ax_main.legend(loc="best", ncol=2, frameon=False)

        # Ensure y starts at 0
        ax_main.set_ylim(bottom=0)

        # Residuals panel
        if show_residuals:
            ax_main.set_xlabel("")
            Vtot_obs = self.curves.get("Vtot_obs")
            if visibility.get("Observed", False) and Vtot_obs is not None:
                delta_v = Vobs - Vtot_obs
                ax_res.errorbar(
                    R, delta_v,
                    yerr=np.nan_to_num(eV, nan=0.0),
                    fmt="o", ms=3, capsize=2,
                    elinewidth=0.6, alpha=0.85,
                    color=ROTATION_COLORS["Observed"],
                    zorder=5
                )
                ax_res.axhline(0, color="#888888", linewidth=1, alpha=0.7)

            ax_res.set_xlabel("Radius R [kpc]")
            ax_res.set_ylabel("ΔV [km/s]")
            ax_res.grid(True, alpha=0.25)
        else:
            ax_res.set_visible(False)
            ax_main.set_xlabel("Radius R [kpc]")

        self._update_fit_stats()
        self._setup_mplcursors()

        self.canvas.draw()

    def _setup_mplcursors(self):
        """Setup mplcursors for interactive data point selection."""
        if not HAS_MPLCURSORS or self._scatter_artist is None:
            return

        # Remove previous cursor
        if self._cursor is not None:
            try:
                self._cursor.remove()
            except Exception:
                pass
            self._cursor = None

        try:
            self._cursor = mplcursors.cursor(
                self._scatter_artist,
                hover=False,
                highlight=True,
                highlight_kwargs={"s": 80, "edgecolors": "red", "linewidths": 2, "facecolors": "none"}
            )

            @self._cursor.connect("add")
            def on_add(sel):
                idx = sel.index
                R = self.curves["R"]
                Vobs = self.curves["Vobs"]
                eV = self.curves["eV"]

                if idx < len(R):
                    lines = [
                        f"Point {idx + 1}",
                        f"R = {R[idx]:.2f} kpc",
                        f"V = {Vobs[idx]:.1f} km/s",
                        f"error = {eV[idx]:.1f} km/s",
                    ]

                    # Add Vtot comparison if available
                    Vtot_obs = self.curves.get("Vtot_obs")
                    if Vtot_obs is not None and idx < len(Vtot_obs):
                        residual = Vobs[idx] - Vtot_obs[idx]
                        lines.append(f"V_model = {Vtot_obs[idx]:.1f} km/s")
                        lines.append(f"residual = {residual:+.1f} km/s")

                    sel.annotation.set_text("\n".join(lines))
                    sel.annotation.set_color("black")
                    sel.annotation.get_bbox_patch().set(
                        facecolor="white", alpha=0.95, edgecolor="gray"
                    )

        except Exception:
            self._cursor = None

    def _update_fit_stats(self):
        """Update chi-squared statistics for the current fit."""
        if self.curves is None:
            self.rotation_controls.update_chi2(None, None, 0)
            return

        Vobs = self.curves.get("Vobs")
        Vtot_obs = self.curves.get("Vtot_obs")
        eV = self.curves.get("eV")

        if Vtot_obs is None or Vobs is None or eV is None:
            self.rotation_controls.update_chi2(None, None, 0)
            return

        valid = np.isfinite(Vobs) & np.isfinite(Vtot_obs) & (eV > 0)
        if not np.any(valid):
            self.rotation_controls.update_chi2(None, None, 0)
            return

        residuals = (Vobs[valid] - Vtot_obs[valid]) / eV[valid]
        chi2 = float(np.sum(residuals**2))
        n = int(np.sum(valid))
        dof = max(n - 2, 1)
        reduced = chi2 / dof
        self.rotation_controls.update_chi2(chi2, reduced, n)

    def _on_tab_changed(self, index: int):
        """Refresh galaxy view when the tab becomes visible."""
        if self.controls_tabs.currentIndex() != index:
            self.controls_tabs.setCurrentIndex(index)
        if self.tabs.widget(index) == self.galaxy_view_widget and self._galaxy_view_dirty:
            self._update_galaxy_3d_view()

    def _on_controls_tab_changed(self, index: int):
        """Sync plot tab with controls tab selection."""
        if self.tabs.currentIndex() != index:
            self.tabs.setCurrentIndex(index)

    def _on_galaxy_3d_options_changed(self, options: dict):
        """Handle 3D galaxy view option changes."""
        self.galaxy_3d_viewer.set_render_options(**options)

    def _on_galaxy_3d_view_preset(self, view: str):
        """Handle 3D view preset request."""
        self.galaxy_3d_viewer.set_view(view)

    def _on_galaxy_3d_screenshot(self):
        """Handle screenshot request."""
        if self.current_galaxy is None:
            QMessageBox.information(self, "No Galaxy", "Please select a galaxy first.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot",
            f"{self.current_galaxy}_3d.png",
            "PNG Files (*.png);;All Files (*)"
        )
        if filename:
            self.galaxy_3d_viewer.save_screenshot(filename)

    def _update_galaxy_3d_view(self):
        """Render interactive 3D galaxy using PyVista."""
        if self.current_data is None or self.current_galaxy is None:
            self.galaxy_3d_viewer.clear()
            return

        if "R" not in self.current_data.columns:
            return

        R = self.current_data["R"].to_numpy(float)
        sb_disk = self.current_data.get("SBdisk")
        sb_bul = self.current_data.get("SBbul")

        if sb_disk is None or sb_bul is None:
            return

        sb_disk = sb_disk.to_numpy(float)
        sb_bul = sb_bul.to_numpy(float)

        # Sort by radius
        order = np.argsort(R)
        R = R[order]
        sb_disk = np.nan_to_num(sb_disk[order], nan=0.0)
        sb_bul = np.nan_to_num(sb_bul[order], nan=0.0)

        # Get M/L values
        ml_disk, ml_bulge = self.rotation_controls.get_ml_values()

        # Get disk scale length from Table1 if available
        h_R = None
        table1_entry = self._table1_lookup.get(self._normalize_galaxy_name(self.current_galaxy))
        if table1_entry is not None:
            rdisk = table1_entry.get("Rdisk")
            try:
                h_R = float(rdisk)
            except (TypeError, ValueError):
                h_R = None

        # Build halo parameters if available
        halo_params = None
        if self.curves is not None:
            halo_model = self.rotation_controls.get_halo_model()
            p1, p2 = self.curves.get("params", (None, None))
            if p1 is not None and p2 is not None:
                halo_params = {
                    "model": halo_model,
                    "p1": p1,
                    "p2": p2,
                    "H0": self.rotation_controls.get_cosmology_params().get("H0", 67.4),
                }

        # Get current 3D render options
        options = self.galaxy_3d_controls.get_options()

        # Render galaxy
        self.galaxy_3d_viewer.render_galaxy(
            R=R,
            SBdisk=sb_disk,
            SBbul=sb_bul,
            ml_disk=ml_disk,
            ml_bulge=ml_bulge,
            h_R=h_R,
            halo_params=halo_params,
            options=options,
        )

        self._galaxy_view_dirty = False

    def on_settings_changed(self):
        """Handle settings changes from main window."""
        self.settings = get_settings()
        # Update theme for 3D viewer
        self.galaxy_3d_viewer.set_theme(self.settings.theme)
        if self.curves:
            self._update_plot()
