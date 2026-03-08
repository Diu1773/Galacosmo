"""Control panel widgets for rotation curve window."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QCheckBox, QRadioButton,
    QComboBox, QListWidget, QListWidgetItem,
    QGroupBox, QDoubleSpinBox, QSpinBox, QColorDialog, QMenu,
    QDialog, QDialogButtonBox,
)

from ...config import get_settings
from ...config.constants import COSMO_PRESETS
from ...config.palettes import ROTATION_COLORS


class RotationControlPanel(QWidget):
    """Control panel for rotation curve fitting."""

    # Signals
    load_data_requested = pyqtSignal()
    pick_galaxy_requested = pyqtSignal()
    delete_files_requested = pyqtSignal()
    clear_files_requested = pyqtSignal()
    halo_model_changed = pyqtSignal(str)
    ml_changed = pyqtSignal(float, float)
    curves_visibility_changed = pyqtSignal(dict)
    curve_style_changed = pyqtSignal()
    cosmology_changed = pyqtSignal()
    rotation_settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = get_settings()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Data section
        data_group = QGroupBox("데이터")
        data_layout = QVBoxLayout(data_group)

        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("파일 불러오기")
        self.btn_load.setToolTip("SPARC Table1, Table2 파일을 선택합니다.")
        btn_layout.addWidget(self.btn_load)

        self.btn_pick = QPushButton("은하 선택")
        self.btn_pick.setToolTip("SPARC 목록에서 은하를 고릅니다.")
        btn_layout.addWidget(self.btn_pick)
        data_layout.addLayout(btn_layout)

        self.lbl_galaxy = QLabel("선택된 은하 없음")
        self.lbl_galaxy.setObjectName("subtitle")
        data_layout.addWidget(self.lbl_galaxy)

        files_label = QLabel("불러온 파일")
        files_label.setObjectName("subtitle")
        data_layout.addWidget(files_label)

        self.list_files = QListWidget()
        self.list_files.setMaximumHeight(120)
        data_layout.addWidget(self.list_files)

        file_btn_layout = QHBoxLayout()
        self.btn_del_sel = QPushButton("선택 삭제")
        self.btn_del_all = QPushButton("전체 삭제")
        self.btn_del_all.setObjectName("danger")
        file_btn_layout.addWidget(self.btn_del_sel)
        file_btn_layout.addWidget(self.btn_del_all)
        data_layout.addLayout(file_btn_layout)

        layout.addWidget(data_group)

        # Rotation curve section
        rotation_group = QGroupBox("회전곡선 탐구")
        rotation_layout = QVBoxLayout(rotation_group)

        rotation_layout.addWidget(QLabel("헤일로 모델:"))
        self.rb_iso = QRadioButton("Isothermal (ISO)")
        self.rb_nfw = QRadioButton("NFW")
        self.btn_nfw_settings = QPushButton("NFW 설정")

        if self.settings.halo_model == "NFW":
            self.rb_nfw.setChecked(True)
        else:
            self.rb_iso.setChecked(True)
        self.btn_nfw_settings.setEnabled(self.rb_nfw.isChecked())

        rotation_layout.addWidget(self.rb_iso)
        nfw_layout = QHBoxLayout()
        nfw_layout.addWidget(self.rb_nfw)
        nfw_layout.addWidget(self.btn_nfw_settings)
        rotation_layout.addLayout(nfw_layout)

        ml_layout = QGridLayout()
        ml_layout.addWidget(QLabel("M/L Disk:"), 0, 0)
        self.sp_ml_disk = QDoubleSpinBox()
        self.sp_ml_disk.setRange(0.1, 5.0)
        self.sp_ml_disk.setDecimals(2)
        self.sp_ml_disk.setSingleStep(0.1)
        self.sp_ml_disk.setValue(self.settings.ml_disk)
        ml_layout.addWidget(self.sp_ml_disk, 0, 1)

        ml_layout.addWidget(QLabel("M/L Bulge:"), 1, 0)
        self.sp_ml_bulge = QDoubleSpinBox()
        self.sp_ml_bulge.setRange(0.1, 5.0)
        self.sp_ml_bulge.setDecimals(2)
        self.sp_ml_bulge.setSingleStep(0.1)
        self.sp_ml_bulge.setValue(self.settings.ml_bulge)
        ml_layout.addWidget(self.sp_ml_bulge, 1, 1)
        rotation_layout.addLayout(ml_layout)

        layout.addWidget(rotation_group)

        # Curves visibility section
        curves_group = QGroupBox("표시 곡선")
        curves_layout = QVBoxLayout(curves_group)

        self.curve_checkboxes = {}
        self.curve_visibility_keys = {}
        self.curve_color_keys = {}
        curve_items = [
            ("Observed + Total", True, ["Observed", "Total"]),
            ("Disk", False, ["Disk"]),
            ("Bulge", False, ["Bulge"]),
            ("Gas", False, ["Gas"]),
            ("Baryons", True, ["Baryons"]),
            ("Halo", True, ["Halo"]),
        ]

        for name, default, color_keys in curve_items:
            cb = QCheckBox(name)
            cb.setChecked(default)
            cb.setContextMenuPolicy(Qt.CustomContextMenu)
            cb.customContextMenuRequested.connect(
                lambda pos, box=cb: self._on_curve_color_menu(box, pos)
            )

            self.curve_checkboxes[name] = cb
            self.curve_visibility_keys[name] = list(color_keys)
            self.curve_color_keys[name] = list(color_keys)

            self._update_curve_checkbox_style(name)
            self._update_curve_checkbox_tooltip(name)

            curves_layout.addWidget(cb)

        # Formula hints
        hint1 = QLabel("Baryons = √(Disk² + Bulge² + Gas²)")
        hint1.setObjectName("subtitle")
        curves_layout.addWidget(hint1)

        hint2 = QLabel("Total = √(Baryons² + Halo²)")
        hint2.setObjectName("subtitle")
        curves_layout.addWidget(hint2)

        layout.addWidget(curves_group)

        # Fit results section
        self.results_group = QGroupBox("적합 결과")
        self.results_layout = QVBoxLayout(self.results_group)
        self.lbl_param1 = QLabel("—")
        self.lbl_param2 = QLabel("—")
        self.results_layout.addWidget(self.lbl_param1)
        self.results_layout.addWidget(self.lbl_param2)
        self.lbl_chi2 = QLabel("χ²: —")
        self.results_layout.addWidget(self.lbl_chi2)

        layout.addWidget(self.results_group)

        layout.addStretch()

    def _connect_signals(self):
        """Connect internal signals."""
        self.btn_load.clicked.connect(self.load_data_requested)
        self.btn_pick.clicked.connect(self.pick_galaxy_requested)
        self.btn_del_sel.clicked.connect(self.delete_files_requested)
        self.btn_del_all.clicked.connect(self.clear_files_requested)

        self.rb_iso.toggled.connect(self._on_halo_changed)
        self.rb_nfw.toggled.connect(self._on_halo_changed)
        self.btn_nfw_settings.clicked.connect(self._open_nfw_settings)

        self.sp_ml_disk.valueChanged.connect(self._on_ml_changed)
        self.sp_ml_bulge.valueChanged.connect(self._on_ml_changed)
        for cb in self.curve_checkboxes.values():
            cb.stateChanged.connect(self._on_visibility_changed)

    def _on_halo_changed(self):
        """Handle halo model change."""
        model = "ISO" if self.rb_iso.isChecked() else "NFW"
        self.settings.halo_model = model
        self.btn_nfw_settings.setEnabled(model == "NFW")
        self.halo_model_changed.emit(model)

    def _on_ml_changed(self):
        """Handle M/L change."""
        self.settings.ml_disk = self.sp_ml_disk.value()
        self.settings.ml_bulge = self.sp_ml_bulge.value()
        self.ml_changed.emit(
            self.sp_ml_disk.value(),
            self.sp_ml_bulge.value()
        )

    def _on_visibility_changed(self):
        """Handle curve visibility change."""
        visibility = {}
        for name, cb in self.curve_checkboxes.items():
            for key in self.curve_visibility_keys.get(name, [name]):
                visibility[key] = cb.isChecked()
        self.curves_visibility_changed.emit(visibility)

    def _update_curve_checkbox_style(self, name: str):
        """Update checkbox indicator color."""
        cb = self.curve_checkboxes.get(name)
        if not cb:
            return
        color_keys = self.curve_color_keys.get(name, [name])
        indicator_key = color_keys[-1] if name == "Observed + Total" else color_keys[0]
        color = ROTATION_COLORS.get(indicator_key, "#000000")
        cb.setStyleSheet(
            f"QCheckBox::indicator:checked {{ background-color: {color}; }}"
        )

    def _update_curve_checkbox_tooltip(self, name: str):
        """Update tooltip with curve colors."""
        cb = self.curve_checkboxes.get(name)
        if not cb:
            return
        color_keys = self.curve_color_keys.get(name, [name])
        if name == "Observed + Total":
            obs = ROTATION_COLORS.get("Observed", "#000000")
            total = ROTATION_COLORS.get("Total", "#000000")
            cb.setToolTip(
                f"Observed: {obs}\nTotal: {total}\n우클릭하여 색상을 변경할 수 있습니다."
            )
        else:
            key = color_keys[0]
            color = ROTATION_COLORS.get(key, "#000000")
            cb.setToolTip(f"{key} color: {color}\n우클릭하여 색상을 변경할 수 있습니다.")

    def _on_curve_color_menu(self, checkbox: QCheckBox, pos):
        """Open color picker for curve colors."""
        name = checkbox.text()
        color_keys = self.curve_color_keys.get(name, [name])
        if name == "Observed + Total":
            menu = QMenu(self)
            act_obs = menu.addAction("Observed 색상 설정")
            act_tot = menu.addAction("Total 색상 설정")
            action = menu.exec_(checkbox.mapToGlobal(pos))
            if action == act_obs:
                self._pick_curve_color("Observed")
            elif action == act_tot:
                self._pick_curve_color("Total")
            return

        self._pick_curve_color(color_keys[0])

    def _pick_curve_color(self, key: str):
        """Pick and apply a curve color."""
        current = ROTATION_COLORS.get(key, "#000000")
        color = QColorDialog.getColor()
        if not color.isValid():
            return
        new_color = color.name()
        ROTATION_COLORS[key] = new_color
        for name in self.curve_checkboxes:
            if key in self.curve_color_keys.get(name, []):
                self._update_curve_checkbox_style(name)
                self._update_curve_checkbox_tooltip(name)
        self.curve_style_changed.emit()

    def _open_nfw_settings(self):
        """Open NFW cosmology settings dialog."""
        dialog = NFWSettingsDialog(self.settings, self)
        if dialog.exec_():
            self.cosmology_changed.emit()
            if self.rb_nfw.isChecked():
                self.rotation_settings_changed.emit()

    def set_galaxy_name(self, name: str):
        """Update displayed galaxy name."""
        if name:
            self.lbl_galaxy.setText(f"은하: {name}")
        else:
            self.lbl_galaxy.setText("선택된 은하 없음")

    def set_fit_results(self, model: str, p1: float, p2: float):
        """Update fit results display."""
        if model.upper() == "ISO":
            self.lbl_param1.setText(f"ρ₀ = {p1:.2e} M☉/kpc³")
            self.lbl_param2.setText(f"rc = {p2:.2f} kpc")
        else:
            self.lbl_param1.setText(f"V₂₀₀ = {p1:.1f} km/s")
            self.lbl_param2.setText(f"c = {p2:.2f}")

    def update_chi2(self, chi2: float, reduced: float, n: int):
        """Update chi-squared display."""
        if chi2 is None or n == 0:
            self.lbl_chi2.setText("χ²: —")
        else:
            self.lbl_chi2.setText(
                f"χ² = {chi2:.1f} (reduced: {reduced:.2f}) | 데이터 수={n}"
            )

    def set_loaded_files(self, files: list):
        """Replace the loaded file list."""
        self.list_files.clear()
        for label, path in files:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, path)
            self.list_files.addItem(item)

    def clear_loaded_files(self):
        """Clear the loaded file list."""
        self.list_files.clear()

    def get_selected_files(self) -> list:
        """Return selected file paths."""
        selected = []
        for item in self.list_files.selectedItems():
            selected.append(item.data(Qt.UserRole))
        return selected

    def get_halo_model(self) -> str:
        """Get current halo model."""
        return "ISO" if self.rb_iso.isChecked() else "NFW"

    def get_ml_values(self) -> tuple:
        """Get current M/L values."""
        return self.sp_ml_disk.value(), self.sp_ml_bulge.value()

    def get_cosmology_params(self) -> dict:
        """Get current cosmology settings for halo calculations."""
        return {
            "H0": self.settings.H0,
            "Omega_m": self.settings.Omega_m,
            "Omega_L": self.settings.Omega_L,
            "use_Hz": self.settings.get("rotation_curve", "use_Hz", default=False),
        }

    def get_visibility(self) -> dict:
        """Get current curve visibility settings."""
        visibility = {}
        for name, cb in self.curve_checkboxes.items():
            for key in self.curve_visibility_keys.get(name, [name]):
                visibility[key] = cb.isChecked()
        return visibility

class GalaxyViewControlPanel(QWidget):
    """Control panel for galaxy view rendering."""

    galaxy_view_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        galaxy_group = QGroupBox("은하 보기")
        galaxy_layout = QVBoxLayout(galaxy_group)

        galaxy_layout.addWidget(QLabel("구성 성분:"))
        self.cmb_component = QComboBox()
        self.cmb_component.addItem("전체 (Disk + Bulge)", "total")
        self.cmb_component.addItem("Disk만", "disk")
        self.cmb_component.addItem("Bulge만", "bulge")
        galaxy_layout.addWidget(self.cmb_component)

        grid_layout = QGridLayout()
        grid_layout.addWidget(QLabel("격자 크기:"), 0, 0)
        self.sp_grid = QSpinBox()
        self.sp_grid.setRange(40, 200)
        self.sp_grid.setSingleStep(10)
        self.sp_grid.setValue(120)
        grid_layout.addWidget(self.sp_grid, 0, 1)
        galaxy_layout.addLayout(grid_layout)

        note = QLabel("Table2의 SBdisk/SBbul을 사용합니다. 가스 분포는 제공되지 않습니다.")
        note.setObjectName("subtitle")
        note.setWordWrap(True)
        galaxy_layout.addWidget(note)

        layout.addWidget(galaxy_group)
        layout.addStretch()

    def _connect_signals(self):
        self.cmb_component.currentIndexChanged.connect(self.galaxy_view_changed)
        self.sp_grid.valueChanged.connect(self.galaxy_view_changed)

    def get_galaxy_view_options(self) -> dict:
        """Get current galaxy view settings."""
        return {
            "component": self.cmb_component.currentData(),
            "grid_size": self.sp_grid.value(),
        }


class NFWSettingsDialog(QDialog):
    """Dialog for NFW cosmology settings."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("NFW 설정")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        groups_layout = QHBoxLayout()
        layout.addLayout(groups_layout)

        preset_group = QGroupBox("프리셋 및 옵션")
        preset_layout = QVBoxLayout(preset_group)

        preset_layout.addWidget(QLabel("프리셋:"))
        self.cmb_preset = QComboBox()
        self.cmb_preset.addItem("Custom", "custom")
        for key, preset in COSMO_PRESETS.items():
            self.cmb_preset.addItem(preset["name"], key)
        preset_key = self.settings.get("cosmology", "preset", default="custom")
        preset_idx = self.cmb_preset.findData(preset_key)
        if preset_idx >= 0:
            self.cmb_preset.setCurrentIndex(preset_idx)
        preset_layout.addWidget(self.cmb_preset)

        self.chk_use_Hz = QCheckBox("H₀ 대신 H(z) 사용")
        self.chk_use_Hz.setChecked(
            self.settings.get("rotation_curve", "use_Hz", default=False)
        )
        preset_layout.addWidget(self.chk_use_Hz)

        self.lbl_Ok = QLabel("Ωk: 0.0000")
        self.lbl_Ok.setObjectName("subtitle")
        preset_layout.addWidget(self.lbl_Ok)
        preset_layout.addStretch()

        param_group = QGroupBox("매개변수")
        param_layout = QGridLayout(param_group)

        param_layout.addWidget(QLabel("H₀ (km/s/Mpc):"), 0, 0)
        self.sp_H0 = QDoubleSpinBox()
        self.sp_H0.setRange(30, 100)
        self.sp_H0.setDecimals(1)
        self.sp_H0.setSingleStep(0.5)
        self.sp_H0.setValue(self.settings.H0)
        param_layout.addWidget(self.sp_H0, 0, 1)

        param_layout.addWidget(QLabel("Ωm:"), 1, 0)
        self.sp_Om = QDoubleSpinBox()
        self.sp_Om.setRange(0, 1)
        self.sp_Om.setDecimals(4)
        self.sp_Om.setSingleStep(0.01)
        self.sp_Om.setValue(self.settings.Omega_m)
        param_layout.addWidget(self.sp_Om, 1, 1)

        param_layout.addWidget(QLabel("ΩΛ:"), 2, 0)
        self.sp_Ol = QDoubleSpinBox()
        self.sp_Ol.setRange(0, 1)
        self.sp_Ol.setDecimals(4)
        self.sp_Ol.setSingleStep(0.01)
        self.sp_Ol.setValue(self.settings.Omega_L)
        param_layout.addWidget(self.sp_Ol, 2, 1)

        groups_layout.addWidget(preset_group, stretch=1)
        groups_layout.addWidget(param_group, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        self.cmb_preset.currentIndexChanged.connect(self._on_preset_changed)
        self.sp_Om.valueChanged.connect(self._update_omega_k)
        self.sp_Ol.valueChanged.connect(self._update_omega_k)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        self._update_omega_k()

    def _update_omega_k(self):
        Ok = 1.0 - self.sp_Om.value() - self.sp_Ol.value()
        self.lbl_Ok.setText(f"Ωk: {Ok:.4f}")

    def _on_preset_changed(self):
        key = self.cmb_preset.currentData()
        if key and key != "custom" and key in COSMO_PRESETS:
            preset = COSMO_PRESETS[key]
            self.sp_H0.setValue(preset["H0"])
            self.sp_Om.setValue(preset["Omega_m"])
            self.sp_Ol.setValue(preset["Omega_L"])
            self._update_omega_k()

    def _on_accept(self):
        self.settings.H0 = self.sp_H0.value()
        self.settings.Omega_m = self.sp_Om.value()
        self.settings.Omega_L = self.sp_Ol.value()
        self.settings.set(
            "rotation_curve", "use_Hz", value=self.chk_use_Hz.isChecked()
        )
        preset_key = self.cmb_preset.currentData() or "custom"
        self.settings.set("cosmology", "preset", value=preset_key)
        self.accept()
