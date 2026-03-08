"""Hubble diagram analysis window."""

import os
import numpy as np
import pandas as pd

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFileDialog, QMessageBox, QSplitter, QColorDialog,
    QScrollArea,
)
from ...config import get_settings
from ...config.palettes import DataStyler
from ...data import load_sn_table, load_union21_latex, get_default_data_dir
from ...models import mu_theory
from ...utils import smart_downsample, allocate_points, get_cosmo_cache
from ..widgets import DualPanelCanvas
from .data_manager import DatasetManager
from .models_dialog import CosmologyModelsDialog
from .controls import HubbleControlPanel

try:
    import mplcursors
    HAS_MPLCURSORS = True
except ImportError:
    HAS_MPLCURSORS = False


class HubbleDiagramWindow(QMainWindow):
    """Window for SN Ia Hubble diagram analysis."""

    def __init__(self, parent=None, app_icon=None):
        super().__init__(parent)
        self.settings = get_settings()
        self.app_icon = app_icon

        # Data
        self.data_manager = DatasetManager(self.settings.palette)
        self.cosmo_cache = get_cosmo_cache()

        # Union2.1 specific data storage
        self.union21_df = None  # Full Union2.1 DataFrame
        self.union21_path = None  # Path to loaded Union2.1 file
        self._scatter_artists = []  # For mplcursors interaction
        self._cursor = None  # mplcursors cursor object

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.setWindowTitle("SN Ia 허블 다이어그램")
        self.resize(1300, 850)

        if self.app_icon:
            self.setWindowIcon(self.app_icon)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Left: Dual panel plot
        self.canvas = DualPanelCanvas(figsize=(10, 8), height_ratios=(3, 1))
        self.canvas.set_help_text(
            "허블 다이어그램 도움말\n\n"
            "- 이 창은 암흑물질 탐구의 확장 활동으로 사용할 수 있습니다.\n"
            "- Preset은 기준 우주론(Reference)의 기준선을 설정합니다.\n"
            "- Residuals는 관측 거리 모듈러스와 기준 모형의 차이 Δμ를 보여줍니다.\n"
            "- Cosmology Models는 비교용 곡선이며 Manage Models에서 조정할 수 있습니다.\n"
            "- 점 개수와 다운샘플링 설정은 성능과 가독성에 영향을 줍니다.\n"
            "- 로그 축은 z > 0 자료에서만 의미가 있습니다.\n"
        )
        splitter.addWidget(self.canvas)

        # Right: Controls (wrapped in scroll area for vertical resizing)
        self.controls = HubbleControlPanel()
        controls_scroll = QScrollArea()
        controls_scroll.setWidget(self.controls)
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setFrameShape(QScrollArea.NoFrame)
        splitter.addWidget(controls_scroll)

        splitter.setSizes([800, 350])

    def _connect_signals(self):
        """Connect control signals."""
        self.controls.add_files_requested.connect(self._on_add_files)
        self.controls.delete_selected_requested.connect(self._on_delete_selected)
        self.controls.delete_all_requested.connect(self._on_delete_all)
        self.controls.dataset_toggled.connect(self._on_dataset_toggled)
        self.controls.dataset_color_requested.connect(self._on_dataset_color)
        self.controls.cosmology_changed.connect(self._on_redraw)
        self.controls.display_options_changed.connect(self._on_redraw)
        self.controls.model_visibility_changed.connect(self._on_redraw)
        self.controls.manage_models_requested.connect(self._open_models_dialog)
        self.controls.exclude_cuts_changed.connect(self._on_exclude_cuts_changed)

    def _on_add_files(self):
        """Handle add files request - auto-detect format."""
        default_dir = get_default_data_dir()
        start_dir = str(default_dir) if default_dir else ""
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "SN Ia 데이터 파일 선택",
            start_dir,
            "All Supported (*.csv *.txt *.dat *.tex);;LaTeX (*.tex);;Data (*.csv *.txt *.dat);;All Files (*)"
        )

        if not paths:
            return

        # Check if any .tex file (Union2.1 format)
        tex_files = [p for p in paths if p.lower().endswith(".tex")]
        other_files = [p for p in paths if not p.lower().endswith(".tex")]

        # Load Union2.1 .tex files with sample-based coloring
        for path in tex_files:
            self._load_union21_file(path)

        # Load regular data files
        added = 0
        for path in other_files:
            try:
                df = load_sn_table(path)
                label = os.path.basename(path)
                actual_label = self.data_manager.add_dataset(label, df)
                self.controls.add_dataset_item(
                    actual_label,
                    self.data_manager.get_dataset(actual_label)["color"]
                )
                added += 1
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "불러오기 오류",
                    f"{os.path.basename(path)} 파일을 불러오는 중 오류가 발생했습니다.\n{e}"
                )

        if added > 0 or tex_files:
            self._update_info()
            self._redraw()

    def _load_union21_file(self, path: str):
        """Load Union2.1 .tex file with sample-based coloring."""
        try:
            exclude_cuts = self.controls.get_exclude_cuts_failed()
            df = load_union21_latex(path, exclude_cuts_failed=exclude_cuts)

            if len(df) == 0:
                QMessageBox.warning(
                    self,
                    "데이터 없음",
                    f"{os.path.basename(path)} 안에 사용할 수 있는 데이터가 없습니다."
                )
                return

            # Store for interactive features and reload on exclude_cuts toggle
            self.union21_df = df
            self.union21_path = path

            # Create styler for sample-based colors
            styler = DataStyler(self.settings.palette)

            # Group by sample and add each as a dataset
            sample_ids = sorted(df["sample_id"].unique())
            for sample_id in sample_ids:
                subset = df[df["sample_id"] == sample_id].copy()
                paper_name = subset["paper_name"].iloc[0]
                label = f"{sample_id}: {paper_name}"

                style = styler.get_style(sample_id - 1)
                actual_label = self.data_manager.add_dataset(label, subset, enabled=True)
                self.data_manager.set_color(actual_label, style["color"])
                self.controls.add_dataset_item(actual_label, style["color"], enabled=True)

        except Exception as e:
            QMessageBox.warning(
                self,
                "불러오기 오류",
                f"{os.path.basename(path)} 파일을 불러오는 중 오류가 발생했습니다.\n{e}"
            )

    def _on_exclude_cuts_changed(self, exclude: bool):
        """Handle exclude cuts failed toggle - reload Union2.1 if loaded."""
        if self.union21_path is not None:
            try:
                df = load_union21_latex(self.union21_path, exclude_cuts_failed=exclude)
                self.union21_df = df

                # Rebuild datasets
                self.data_manager.clear()
                self.controls.clear_dataset_list()

                styler = DataStyler(self.settings.palette)
                sample_ids = sorted(df["sample_id"].unique())

                for sample_id in sample_ids:
                    subset = df[df["sample_id"] == sample_id].copy()
                    paper_name = subset["paper_name"].iloc[0]
                    label = f"{sample_id}: {paper_name}"
                    style = styler.get_style(sample_id - 1)

                    actual_label = self.data_manager.add_dataset(label, subset, enabled=True)
                    self.data_manager.set_color(actual_label, style["color"])
                    self.controls.add_dataset_item(actual_label, style["color"], enabled=True)

                self._update_info()
                self._redraw()
            except Exception:
                pass

    def _on_delete_selected(self):
        """Handle delete selected request."""
        labels = self.controls.get_selected_datasets()
        for label in labels:
            self.data_manager.remove_dataset(label)
            self.controls.remove_dataset_item(label)
        self._update_info()
        self._redraw()

    def _on_delete_all(self):
        """Handle delete all request."""
        self.data_manager.clear()
        self.controls.clear_dataset_list()
        self._update_info()
        self._redraw()

    def _on_dataset_toggled(self, label: str, enabled: bool):
        """Handle dataset enable/disable."""
        self.data_manager.set_enabled(label, enabled)
        self._update_info()
        self._redraw()

    def _on_dataset_color(self):
        """Handle dataset color change."""
        labels = self.controls.get_selected_datasets()
        if not labels:
            QMessageBox.information(self, "선택 없음", "색상을 바꿀 데이터셋을 선택하세요.")
            return

        color = QColorDialog.getColor(parent=self)
        if not color.isValid():
            return

        color_hex = color.name()
        for label in labels:
            self.data_manager.set_color(label, color_hex)
            self.controls.set_dataset_color(label, color_hex)

        self._redraw()

    def _on_redraw(self, *args):
        """Trigger redraw."""
        self._redraw()

    def _open_models_dialog(self):
        """Open model manager dialog."""
        dialog = CosmologyModelsDialog(self)
        if dialog.exec_():
            self.controls.reload_models()
            self._redraw()

    def _update_info(self):
        """Update info display."""
        n_datasets = len(self.data_manager)
        enabled = self.data_manager.get_enabled_datasets()
        n_enabled = len(enabled)
        n_total = self.data_manager.get_total_points(enabled_only=True)

        # Calculate shown points
        max_points = self.controls.get_max_points()
        n_shown = min(n_total, max_points)

        self.controls.update_info(n_datasets, n_enabled, n_total, n_shown)

    def _redraw(self):
        """Redraw the plot."""
        ax_main = self.canvas.ax_main
        ax_res = self.canvas.ax_residual
        # Reset to linear before clearing to avoid log-scale warnings.
        ax_main.set_xscale("linear")
        ax_res.set_xscale("linear")
        ax_main.clear()
        ax_res.clear()

        options = self.controls.get_display_options()
        H0 = self.controls.get_H0()
        max_points = self.controls.get_max_points()
        model_visibility = self.controls.get_model_visibility()
        models = self.controls.get_models()

        enabled_datasets = self.data_manager.get_enabled_datasets()

        min_pos_z = None
        max_pos_z = None

        # Calculate point allocation
        datasets_for_alloc = [(label, data["df"]) for label, data in enabled_datasets]
        allocation = allocate_points(datasets_for_alloc, max_points)

        # Reference cosmology for residuals
        ref_Om, ref_Ol = self.controls.get_reference_cosmology()

        all_z = []
        all_mu = []
        all_emu = []

        # Clear previous scatter artists for mplcursors
        self._scatter_artists = []
        self._scatter_data = []  # Store data for each scatter

        # Plot data
        for label, data in enabled_datasets:
            df = data["df"]
            n_points = allocation.get(label, len(df))

            # Downsample
            if n_points < len(df):
                method = options["downsample_method"]
                if method == "log_uniform":
                    df = smart_downsample(df, n_points, key="z", method="log_uniform")
                else:
                    df = smart_downsample(
                        df,
                        n_points,
                        key="z",
                        method=method,
                        use_log=options["log_downsample"],
                    )

            z = df["z"].values
            mu = df["mu"].values
            emu = df["emu"].values if "emu" in df.columns else np.zeros_like(mu)

            all_z.extend(z)
            all_mu.extend(mu)
            all_emu.extend(emu)

            z_pos = z[(z > 0) & np.isfinite(z)]
            if z_pos.size:
                min_z = float(np.nanmin(z_pos))
                max_z = float(np.nanmax(z_pos))
                if min_pos_z is None or min_z < min_pos_z:
                    min_pos_z = min_z
                if max_pos_z is None or max_z > max_pos_z:
                    max_pos_z = max_z

            color = data["color"]
            marker = data["marker"]

            # Main panel
            if options["y_log_dl"]:
                y_main = (mu - 25.0) / 5.0  # log10(D_L)
                yerr_main = emu / 5.0
            else:
                y_main = mu
                yerr_main = emu

            if options["fast_render"] or len(z) > 500:
                scatter = ax_main.scatter(
                    z, y_main, s=9, c=color, marker=marker,
                    alpha=0.7, edgecolors='none', label=label, picker=True
                )
                self._scatter_artists.append(scatter)
                self._scatter_data.append(df.reset_index(drop=True))
            else:
                ax_main.errorbar(
                    z, y_main, yerr=yerr_main,
                    fmt=marker, ms=3, color=color,
                    capsize=1, elinewidth=0.4, alpha=0.8,
                    mew=0, label=label
                )
                # Also add scatter for interactive picking
                scatter = ax_main.scatter(
                    z, y_main, s=9, c=color, marker=marker,
                    alpha=0.0, edgecolors='none', picker=True
                )
                self._scatter_artists.append(scatter)
                self._scatter_data.append(df.reset_index(drop=True))

            # Residual panel
            mu_ref = mu_theory(z, ref_Om, ref_Ol, H0)
            delta_mu = mu - mu_ref

            if options["fast_render"] or len(z) > 500:
                ax_res.scatter(
                    z, delta_mu, s=9, c=color, marker=marker, alpha=0.7, edgecolors='none'
                )
            else:
                ax_res.errorbar(
                    z, delta_mu, yerr=emu,
                    fmt=marker, ms=3, color=color,
                    capsize=1, elinewidth=0.4, alpha=0.8, mew=0
                )

        # Reference curve (preset baseline)
        z_min = 0.01
        z_max = 1.5
        n_points = 500

        if options["cache_cosmo"]:
            z_ref, mu_ref_curve = self.cosmo_cache.get_or_compute(
                ref_Om, ref_Ol, H0, z_min=z_min, z_max=z_max, n_points=n_points
            )
        else:
            z_ref = np.logspace(np.log10(z_min), np.log10(z_max), n_points)
            mu_ref_curve = mu_theory(z_ref, ref_Om, ref_Ol, H0)

        if min_pos_z is None or z_ref[0] < min_pos_z:
            min_pos_z = float(z_ref[0])
        if max_pos_z is None or z_ref[-1] > max_pos_z:
            max_pos_z = float(z_ref[-1])

        # Cosmology curves
        for key, visible in model_visibility.items():
            if not visible:
                continue

            style = models.get(key)
            if not style:
                continue
            Om = style.get("Omega_m", ref_Om)
            Ol = style.get("Omega_L", ref_Ol)

            if options["cache_cosmo"]:
                z_cached, mu_cached = self.cosmo_cache.get_or_compute(
                    Om, Ol, H0, z_min=z_min, z_max=z_max, n_points=n_points
                )
            else:
                z_cached = np.logspace(np.log10(z_min), np.log10(z_max), n_points)
                mu_cached = mu_theory(z_cached, Om, Ol, H0)

            if min_pos_z is None or z_cached[0] < min_pos_z:
                min_pos_z = float(z_cached[0])
            if max_pos_z is None or z_cached[-1] > max_pos_z:
                max_pos_z = float(z_cached[-1])

            if options["y_log_dl"]:
                y_curve = (mu_cached - 25.0) / 5.0
            else:
                y_curve = mu_cached

            ax_main.plot(
                z_cached, y_curve,
                linestyle=style.get("linestyle", "-"),
                linewidth=1.5,
                color=style.get("color", "#666666"),
                label=style.get("label", key),
                zorder=4
            )

            # Residual
            mu_curve = mu_cached
            if z_cached.shape == z_ref.shape and np.array_equal(z_cached, z_ref):
                mu_ref = mu_ref_curve
            else:
                mu_ref = np.interp(z_cached, z_ref, mu_ref_curve)
            ax_res.plot(
                z_cached, mu_curve - mu_ref,
                linestyle=style.get("linestyle", "-"),
                linewidth=1.2,
                color=style.get("color", "#666666"),
                zorder=4
            )

        if options["y_log_dl"]:
            y_ref = (mu_ref_curve - 25.0) / 5.0
        else:
            y_ref = mu_ref_curve

        ref_color = self.settings.get("snia", "reference_color", default="")
        if not ref_color:
            ref_color = "#f0f0f0" if self.settings.theme == "dark" else "#333333"
        ref_linestyle = self.settings.get("snia", "reference_linestyle", default="-.")
        ax_main.plot(
            z_ref, y_ref,
            linestyle=ref_linestyle,
            linewidth=1.8,
            color=ref_color,
            label="Reference (preset)",
            zorder=6,
        )

        # Styling
        if options["log_x"]:
            ax_main.set_xscale("log")
            ax_res.set_xscale("log")
            if min_pos_z is None or max_pos_z is None:
                min_pos_z = z_min
                max_pos_z = z_max
            ax_main.set_xlim(min_pos_z * 0.9, max_pos_z * 1.1)
            ax_res.set_xlim(min_pos_z * 0.9, max_pos_z * 1.1)
        else:
            ax_main.set_xscale("linear")
            ax_res.set_xscale("linear")

        y_label = "log₁₀ D_L (Mpc)" if options["y_log_dl"] else "μ (mag)"
        ax_main.set_ylabel(y_label)
        ax_res.set_ylabel("Δμ vs reference")
        ax_res.set_xlabel("z")

        ax_main.grid(True, alpha=0.3)
        ax_res.grid(True, alpha=0.3)
        ax_res.axhline(0, color=ref_color, lw=0.7, alpha=0.7, linestyle=ref_linestyle)

        handles, labels = ax_main.get_legend_handles_labels()
        legend_items = [
            (h, l) for h, l in zip(handles, labels) if l and not l.startswith("_")
        ]
        if legend_items:
            handles, labels = zip(*legend_items)
            ax_main.legend(handles, labels, loc="best", frameon=False, fontsize=8)
        ax_main.set_title("SN Ia Hubble Diagram")
        ax_main.tick_params(labelbottom=False)

        # Setup mplcursors for interactive data point info
        self._setup_mplcursors()

        self.canvas.draw()

        # Update chi-squared
        self._update_chi2(all_z, all_mu, all_emu, H0, ref_Om, ref_Ol)

    def _setup_mplcursors(self):
        """Setup mplcursors for interactive data point selection."""
        if not HAS_MPLCURSORS or not self._scatter_artists:
            return

        # Remove previous cursor if exists
        if self._cursor is not None:
            try:
                self._cursor.remove()
            except Exception:
                pass
            self._cursor = None

        try:
            self._cursor = mplcursors.cursor(
                self._scatter_artists,
                hover=False,
                highlight=True,
                highlight_kwargs={"s": 50, "edgecolors": "red", "linewidths": 2}
            )

            @self._cursor.connect("add")
            def on_add(sel):
                # Find which scatter and which point
                artist = sel.artist
                idx = sel.index

                # Find the data for this artist
                for i, scatter in enumerate(self._scatter_artists):
                    if scatter is artist:
                        df = self._scatter_data[i]
                        if idx < len(df):
                            row = df.iloc[idx]
                            self._format_annotation(sel, row)
                        break

        except Exception:
            self._cursor = None

    def _format_annotation(self, sel, row):
        """Format the annotation text for a selected data point."""
        lines = []

        # SN name
        if "name" in row.index:
            lines.append(f"SN {row['name']}")

        # Basic info
        lines.append(f"z = {row['z']:.4f}")
        lines.append(f"mu = {row['mu']:.2f} +/- {row.get('emu', 0):.2f}")

        # Union2.1 specific columns
        if "mB" in row.index:
            lines.append(f"mB = {row['mB']:.2f} +/- {row.get('mB_err', 0):.2f}")
        if "stretch" in row.index:
            lines.append(f"x1 = {row['stretch']:.2f} +/- {row.get('stretch_err', 0):.2f}")
        if "color" in row.index and not pd.isna(row["color"]):
            lines.append(f"c = {row['color']:.3f} +/- {row.get('color_err', 0):.3f}")
        if "P_lowmass" in row.index:
            lines.append(f"P_lowmass = {row['P_lowmass']:.3f}")
        if "sample_id" in row.index:
            paper = row.get("paper_name", f"Sample {row['sample_id']}")
            lines.append(f"Sample: {int(row['sample_id'])} ({paper})")
        if "cuts_failed" in row.index and row["cuts_failed"]:
            lines.append(f"Cuts failed: {row['cuts_failed']}")

        sel.annotation.set_text("\n".join(lines))
        sel.annotation.set_color("black")
        sel.annotation.get_bbox_patch().set(
            facecolor="white", alpha=0.95, edgecolor="gray"
        )

    def _update_chi2(self, z, mu, emu, H0, Om, Ol):
        """Calculate and display chi-squared."""
        if len(z) == 0:
            self.controls.update_chi2(None, None, 0, 0)
            return

        z = np.array(z)
        mu = np.array(mu)
        emu = np.array(emu)

        # Compute theoretical values
        mu_th = mu_theory(z, Om, Ol, H0)

        # Chi-squared
        valid = (emu > 0) & np.isfinite(mu) & np.isfinite(mu_th)
        if not np.any(valid):
            self.controls.update_chi2(None, None, 0, 0)
            return

        residuals = (mu[valid] - mu_th[valid]) / emu[valid]
        chi2 = float(np.sum(residuals**2))
        n = int(np.sum(valid))
        dof = max(n - 1, 1)
        reduced = chi2 / dof

        n_sets = len(self.data_manager.get_enabled_datasets())
        self.controls.update_chi2(chi2, reduced, n, n_sets)

    def on_settings_changed(self):
        """Handle settings changes."""
        self.settings = get_settings()
        self.data_manager.set_palette(self.settings.palette)
        self.controls.refresh_dataset_colors(self.data_manager.datasets)
        self._redraw()
