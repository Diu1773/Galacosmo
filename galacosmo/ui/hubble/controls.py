"""Control panel for Hubble diagram window."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QCheckBox, QGroupBox,
    QDoubleSpinBox, QSpinBox, QComboBox,
    QListWidget, QListWidgetItem,
)
from PyQt5.QtGui import QColor

from ...config import get_settings
from ...config.constants import COSMO_PRESETS
from ...config.palettes import DEFAULT_COSMO_STYLES


class HubbleControlPanel(QWidget):
    """Control panel for Hubble diagram analysis."""

    # Signals
    add_files_requested = pyqtSignal()
    delete_selected_requested = pyqtSignal()
    delete_all_requested = pyqtSignal()
    dataset_toggled = pyqtSignal(str, bool)
    dataset_color_requested = pyqtSignal()
    H0_changed = pyqtSignal(float)
    cosmology_changed = pyqtSignal()
    display_options_changed = pyqtSignal()
    model_visibility_changed = pyqtSignal(dict)
    manage_models_requested = pyqtSignal()
    exclude_cuts_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = get_settings()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Data section
        data_group = QGroupBox("Data")
        data_layout = QVBoxLayout(data_group)

        btn_row = QHBoxLayout()
        self.btn_add_files = QPushButton("Add Files")
        self.btn_add_files.setToolTip("Load CSV/TXT/DAT or Union2.1 .tex files")
        self.btn_del_sel = QPushButton("Delete Selected")
        self.btn_set_color = QPushButton("Set Color")
        self.btn_del_all = QPushButton("Delete All")
        self.btn_del_all.setObjectName("danger")
        btn_row.addWidget(self.btn_add_files)
        btn_row.addWidget(self.btn_del_sel)
        btn_row.addWidget(self.btn_set_color)
        btn_row.addWidget(self.btn_del_all)
        data_layout.addLayout(btn_row)

        self.lbl_info = QLabel("No datasets loaded")
        self.lbl_info.setObjectName("subtitle")
        data_layout.addWidget(self.lbl_info)

        # Dataset list
        self.list_datasets = QListWidget()
        self.list_datasets.setMaximumHeight(150)
        data_layout.addWidget(self.list_datasets)

        # Union2.1 specific option
        self.chk_exclude_cuts = QCheckBox("Exclude cuts failed (Union2.1)")
        self.chk_exclude_cuts.setToolTip("Exclude SNe with quality cuts failed flags")
        self.chk_exclude_cuts.setChecked(False)
        data_layout.addWidget(self.chk_exclude_cuts)

        layout.addWidget(data_group)

        # Cosmology section
        cosmo_group = QGroupBox("Cosmology")
        cosmo_layout = QGridLayout(cosmo_group)

        info_ref = QLabel("Reference cosmology (residual baseline)")
        info_ref.setObjectName("subtitle")
        cosmo_layout.addWidget(info_ref, 0, 0, 1, 2)

        cosmo_layout.addWidget(QLabel("Preset:"), 1, 0)
        self.cmb_preset = QComboBox()
        self.cmb_preset.addItem("Custom", "custom")
        for key, preset in COSMO_PRESETS.items():
            self.cmb_preset.addItem(preset["name"], key)
        preset_key = self.settings.get("cosmology", "preset", default="custom")
        preset_idx = self.cmb_preset.findData(preset_key)
        if preset_idx >= 0:
            self.cmb_preset.setCurrentIndex(preset_idx)
        cosmo_layout.addWidget(self.cmb_preset, 1, 1)

        cosmo_layout.addWidget(QLabel("H₀ (km/s/Mpc):"), 2, 0)
        self.sp_H0 = QDoubleSpinBox()
        self.sp_H0.setRange(30, 100)
        self.sp_H0.setDecimals(1)
        self.sp_H0.setSingleStep(0.5)
        self.sp_H0.setValue(self.settings.H0)
        cosmo_layout.addWidget(self.sp_H0, 2, 1)

        cosmo_layout.addWidget(QLabel("Ωm:"), 3, 0)
        self.sp_Om = QDoubleSpinBox()
        self.sp_Om.setRange(0, 1)
        self.sp_Om.setDecimals(4)
        self.sp_Om.setSingleStep(0.01)
        self.sp_Om.setValue(self.settings.Omega_m)
        cosmo_layout.addWidget(self.sp_Om, 3, 1)

        cosmo_layout.addWidget(QLabel("ΩΛ:"), 4, 0)
        self.sp_Ol = QDoubleSpinBox()
        self.sp_Ol.setRange(0, 1)
        self.sp_Ol.setDecimals(4)
        self.sp_Ol.setSingleStep(0.01)
        self.sp_Ol.setValue(self.settings.Omega_L)
        cosmo_layout.addWidget(self.sp_Ol, 4, 1)

        cosmo_layout.addWidget(QLabel("Ωk:"), 5, 0)
        self.lbl_Ok = QLabel("0.0000")
        cosmo_layout.addWidget(self.lbl_Ok, 5, 1)
        self._update_omega_k()

        layout.addWidget(cosmo_group)

        # SN Ia section
        snia_group = QGroupBox("SN Ia")
        snia_layout = QVBoxLayout(snia_group)

        snia_grid = QGridLayout()
        snia_grid.addWidget(QLabel("Max points:"), 0, 0)
        self.sp_max_points = QSpinBox()
        self.sp_max_points.setRange(10, 50000)
        self.sp_max_points.setSingleStep(100)
        self.sp_max_points.setValue(self.settings.max_display_points)
        snia_grid.addWidget(self.sp_max_points, 0, 1)

        snia_grid.addWidget(QLabel("Downsample method:"), 1, 0)
        self.cmb_downsample = QComboBox()
        self.cmb_downsample.addItem("Density-based", "density")
        self.cmb_downsample.addItem("Uniform", "uniform")
        self.cmb_downsample.addItem("Log-uniform", "log_uniform")
        downsample = self.settings.get("snia", "downsample_method", default="density")
        idx = self.cmb_downsample.findData(downsample)
        if idx >= 0:
            self.cmb_downsample.setCurrentIndex(idx)
        snia_grid.addWidget(self.cmb_downsample, 1, 1)
        snia_layout.addLayout(snia_grid)

        self.chk_log_x = QCheckBox("Log scale x-axis")
        self.chk_log_x.setChecked(self.settings.get("snia", "x_log_scale", default=True))
        snia_layout.addWidget(self.chk_log_x)

        self.chk_log_downsample = QCheckBox("Log-spaced downsampling")
        self.chk_log_downsample.setChecked(
            self.settings.get("snia", "use_log_downsample", default=True)
        )
        snia_layout.addWidget(self.chk_log_downsample)

        self.chk_y_log_dl = QCheckBox("Show log₁₀(D_L) instead of μ")
        self.chk_y_log_dl.setChecked(self.settings.get("snia", "y_log_dl", default=False))
        snia_layout.addWidget(self.chk_y_log_dl)

        self.chk_cache = QCheckBox("Cache cosmology curves")
        self.chk_cache.setChecked(self.settings.get("snia", "cache_cosmo", default=True))
        snia_layout.addWidget(self.chk_cache)

        self.chk_fast_render = QCheckBox("Fast rendering")
        self.chk_fast_render.setChecked(
            self.settings.get("snia", "fast_render", default=False)
        )
        snia_layout.addWidget(self.chk_fast_render)

        # Chi-squared display
        self.lbl_chi2 = QLabel("χ²: —")
        snia_layout.addWidget(self.lbl_chi2)

        layout.addWidget(snia_group)

        # Cosmology models section
        models_group = QGroupBox("Cosmology Models")
        models_layout = QVBoxLayout(models_group)

        info_models = QLabel(
            "Comparison models (preset does not change these). "
            "Reference curve is plotted separately."
        )
        info_models.setObjectName("subtitle")
        models_layout.addWidget(info_models)

        btn_models_layout = QHBoxLayout()
        self.btn_manage_models = QPushButton("Manage Models")
        btn_models_layout.addWidget(self.btn_manage_models)
        btn_models_layout.addStretch()
        models_layout.addLayout(btn_models_layout)

        self.models_list_layout = QVBoxLayout()
        models_layout.addLayout(self.models_list_layout)

        self.model_checkboxes = {}
        self.model_defs = {}
        self._build_model_checkboxes()

        layout.addWidget(models_group)

        layout.addStretch()

    def _connect_signals(self):
        """Connect internal signals."""
        self.btn_add_files.clicked.connect(self.add_files_requested)
        self.btn_del_sel.clicked.connect(self.delete_selected_requested)
        self.btn_del_all.clicked.connect(self.delete_all_requested)
        self.btn_set_color.clicked.connect(self.dataset_color_requested)
        self.chk_exclude_cuts.stateChanged.connect(
            lambda state: self.exclude_cuts_changed.emit(state == Qt.Checked)
        )

        self.list_datasets.itemChanged.connect(self._on_item_changed)

        self.cmb_preset.currentIndexChanged.connect(self._on_preset_changed)
        self.sp_H0.valueChanged.connect(self._on_cosmology_changed)
        self.sp_Om.valueChanged.connect(self._on_cosmology_changed)
        self.sp_Ol.valueChanged.connect(self._on_cosmology_changed)

        self.sp_max_points.valueChanged.connect(self._on_display_changed)
        self.cmb_downsample.currentIndexChanged.connect(self._on_display_changed)

        self.chk_log_x.stateChanged.connect(self._on_display_changed)
        self.chk_log_downsample.stateChanged.connect(self._on_display_changed)
        self.chk_y_log_dl.stateChanged.connect(self._on_display_changed)
        self.chk_cache.stateChanged.connect(self._on_display_changed)
        self.chk_fast_render.stateChanged.connect(self._on_display_changed)
        self.btn_manage_models.clicked.connect(self.manage_models_requested)

    def _on_item_changed(self, item: QListWidgetItem):
        """Handle dataset checkbox change."""
        label = item.data(Qt.UserRole)
        enabled = item.checkState() == Qt.Checked
        self.dataset_toggled.emit(label, enabled)

    def _on_preset_changed(self, index):
        key = self.cmb_preset.currentData()
        if key and key != "custom" and key in COSMO_PRESETS:
            preset = COSMO_PRESETS[key]
            self.settings.apply_preset(key)
            self.sp_H0.setValue(preset["H0"])
            self.sp_Om.setValue(preset["Omega_m"])
            self.sp_Ol.setValue(preset["Omega_L"])

    def _on_cosmology_changed(self):
        self.settings.H0 = self.sp_H0.value()
        self.settings.Omega_m = self.sp_Om.value()
        self.settings.Omega_L = self.sp_Ol.value()
        self._update_omega_k()
        self.H0_changed.emit(self.sp_H0.value())
        self.cosmology_changed.emit()

    def _on_display_changed(self):
        self.settings.max_display_points = self.sp_max_points.value()
        self.settings.set("snia", "downsample_method", value=self.cmb_downsample.currentData())
        self.settings.set("snia", "x_log_scale", value=self.chk_log_x.isChecked())
        self.settings.set("snia", "use_log_downsample", value=self.chk_log_downsample.isChecked())
        self.settings.set("snia", "y_log_dl", value=self.chk_y_log_dl.isChecked())
        self.settings.set("snia", "cache_cosmo", value=self.chk_cache.isChecked())
        self.settings.set("snia", "fast_render", value=self.chk_fast_render.isChecked())
        self.display_options_changed.emit()

    def _on_model_visibility_changed(self):
        models = self.settings.get("models", default={})
        visibility = {
            key: cb.isChecked()
            for key, cb in self.model_checkboxes.items()
        }
        for key, enabled in visibility.items():
            if key in models:
                models[key]["enabled"] = enabled
        self.settings.set("models", value=models)

        self.model_defs = models
        self.model_visibility_changed.emit(visibility)

    def _update_omega_k(self):
        Ok = 1.0 - self.sp_Om.value() - self.sp_Ol.value()
        self.lbl_Ok.setText(f"{Ok:.4f}")

    def _build_model_checkboxes(self):
        """Rebuild comparison model checkboxes from settings."""
        while self.models_list_layout.count():
            item = self.models_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        ref_label = "Reference (preset)"
        self.cb_reference = QCheckBox(ref_label)
        self.cb_reference.setChecked(True)
        self.cb_reference.setEnabled(False)
        ref_color = self._get_reference_color()
        self.cb_reference.setStyleSheet(
            f"QCheckBox::indicator {{ width: 14px; height: 14px; border: 1px solid #888; }}"
            f"QCheckBox::indicator:checked {{ background-color: {ref_color}; }}"
            f"QCheckBox::indicator:unchecked {{ background-color: transparent; }}"
        )
        self.models_list_layout.addWidget(self.cb_reference)

        models = self.settings.get("models", default={})
        if not models:
            models = {
                key: {
                    "label": style["label"],
                    "Omega_m": style["Omega_m"],
                    "Omega_L": style["Omega_L"],
                    "color": style["color"],
                    "linestyle": style["linestyle"],
                    "enabled": False,
                }
                for key, style in DEFAULT_COSMO_STYLES.items()
            }
            self.settings.set("models", value=models)

        self.model_defs = models
        self.model_checkboxes = {}
        for key, style in models.items():
            label_text = style.get("label", key)
            Om = float(style.get("Omega_m", 0.0))
            Ol = float(style.get("Omega_L", 0.0))
            label = f"{label_text} (Ωm={Om:.3f}, ΩΛ={Ol:.3f})"
            cb = QCheckBox(label)
            cb.setChecked(bool(style.get("enabled", False)))
            color = style.get("color", "#666666")
            cb.setStyleSheet(
                f"QCheckBox::indicator {{ width: 14px; height: 14px; border: 1px solid #888; }}"
                f"QCheckBox::indicator:checked {{ background-color: {color}; }}"
                f"QCheckBox::indicator:unchecked {{ background-color: transparent; }}"
            )
            cb.stateChanged.connect(self._on_model_visibility_changed)
            self.model_checkboxes[key] = cb
            self.models_list_layout.addWidget(cb)

    def reload_models(self):
        """Reload model list from settings."""
        self._build_model_checkboxes()
        self.model_visibility_changed.emit(self.get_model_visibility())

    def add_dataset_item(self, label: str, color: str, enabled: bool = False):
        """Add a dataset to the list."""
        item = QListWidgetItem(label)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked if enabled else Qt.Unchecked)
        item.setData(Qt.UserRole, label)
        item.setForeground(QColor(color))
        self.list_datasets.addItem(item)

    def remove_dataset_item(self, label: str):
        """Remove a dataset from the list."""
        for i in range(self.list_datasets.count()):
            item = self.list_datasets.item(i)
            if item.data(Qt.UserRole) == label:
                self.list_datasets.takeItem(i)
                break

    def set_dataset_color(self, label: str, color: str):
        """Update dataset color in the list."""
        for i in range(self.list_datasets.count()):
            item = self.list_datasets.item(i)
            if item.data(Qt.UserRole) == label:
                item.setForeground(QColor(color))
                break

    def refresh_dataset_colors(self, datasets: dict):
        """Refresh list item colors from dataset definitions."""
        for i in range(self.list_datasets.count()):
            item = self.list_datasets.item(i)
            label = item.data(Qt.UserRole)
            data = datasets.get(label)
            if data and "color" in data:
                item.setForeground(QColor(data["color"]))

    def clear_dataset_list(self):
        """Clear all datasets from the list."""
        self.list_datasets.clear()

    def get_selected_datasets(self) -> list:
        """Get list of selected dataset labels."""
        selected = []
        for item in self.list_datasets.selectedItems():
            selected.append(item.data(Qt.UserRole))
        return selected

    def update_info(self, n_datasets: int, n_enabled: int, n_total: int, n_shown: int):
        """Update info label."""
        self.lbl_info.setText(
            f"Datasets: {n_datasets} ({n_enabled} enabled) | "
            f"Points: {n_total} → {n_shown}"
        )

    def update_chi2(self, chi2: float, reduced: float, n: int, k: int):
        """Update chi-squared display."""
        if chi2 is None or n == 0:
            self.lbl_chi2.setText("χ²: —")
        else:
            self.lbl_chi2.setText(
                f"χ² = {chi2:.1f} (reduced: {reduced:.2f}) | N={n}, sets={k}"
            )

    def get_H0(self) -> float:
        return self.sp_H0.value()

    def get_reference_cosmology(self) -> tuple:
        """Return (Omega_m, Omega_L) for the reference model."""
        return self.sp_Om.value(), self.sp_Ol.value()

    def get_max_points(self) -> int:
        return self.sp_max_points.value()

    def get_display_options(self) -> dict:
        return {
            "log_x": self.chk_log_x.isChecked(),
            "log_downsample": self.chk_log_downsample.isChecked(),
            "y_log_dl": self.chk_y_log_dl.isChecked(),
            "downsample_method": self.cmb_downsample.currentData(),
            "cache_cosmo": self.chk_cache.isChecked(),
            "fast_render": self.chk_fast_render.isChecked(),
        }

    def get_model_visibility(self) -> dict:
        return {
            key: cb.isChecked()
            for key, cb in self.model_checkboxes.items()
        }

    def get_models(self) -> dict:
        """Return current model definitions."""
        return self.model_defs

    def _get_reference_color(self) -> str:
        color = self.settings.get("snia", "reference_color", default="")
        if color:
            return color
        return "#f0f0f0" if self.settings.theme == "dark" else "#333333"

    def get_exclude_cuts_failed(self) -> bool:
        """Return whether to exclude cuts_failed SNe."""
        return self.chk_exclude_cuts.isChecked()
