"""Dialog for managing cosmology comparison models."""

from __future__ import annotations

from copy import deepcopy

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QWidget, QLabel, QListWidget, QListWidgetItem, QLineEdit,
    QDoubleSpinBox, QComboBox, QPushButton, QColorDialog,
    QCheckBox, QMessageBox,
)

from ...config import get_settings


class CosmologyModelsDialog(QDialog):
    """Manage comparison models stored in settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Cosmology Models")
        self.setMinimumSize(520, 380)

        self.settings = get_settings()
        self.models = deepcopy(self.settings.get("models", default={}))
        self._current_key = None
        self._reference_key = "__reference__"
        self._reference_label = "Reference (preset)"

        self._setup_ui()
        self._load_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "Add or edit comparison models used in the Hubble diagram. "
            "These do not change the reference baseline."
        )
        info.setWordWrap(True)
        info.setObjectName("subtitle")
        layout.addWidget(info)

        content = QHBoxLayout()
        layout.addLayout(content)

        # Left list
        self.list_models = QListWidget()
        self.list_models.currentItemChanged.connect(self._on_selection_changed)
        content.addWidget(self.list_models, stretch=1)

        # Right form
        form_container = QVBoxLayout()
        content.addLayout(form_container, stretch=2)

        form = QFormLayout()
        form_container.addLayout(form)

        self.ed_key = QLineEdit()
        self.ed_key.setReadOnly(True)
        form.addRow("ID", self.ed_key)

        self.ed_label = QLineEdit()
        form.addRow("Label", self.ed_label)

        self.sp_Om = QDoubleSpinBox()
        self.sp_Om.setRange(0.0, 1.0)
        self.sp_Om.setDecimals(4)
        self.sp_Om.setSingleStep(0.01)
        form.addRow("Ωm", self.sp_Om)

        self.sp_Ol = QDoubleSpinBox()
        self.sp_Ol.setRange(0.0, 1.0)
        self.sp_Ol.setDecimals(4)
        self.sp_Ol.setSingleStep(0.01)
        form.addRow("ΩΛ", self.sp_Ol)

        color_row = QHBoxLayout()
        color_row.setContentsMargins(0, 0, 0, 0)
        self.ed_color = QLineEdit()
        self.btn_pick_color = QPushButton("Pick")
        self.btn_pick_color.clicked.connect(self._pick_color)
        color_row.addWidget(self.ed_color)
        color_row.addWidget(self.btn_pick_color)
        color_widget = QWidget()
        color_widget.setLayout(color_row)
        form.addRow("Color", color_widget)

        self.cmb_linestyle = QComboBox()
        self.cmb_linestyle.addItem("Solid (-)", "-")
        self.cmb_linestyle.addItem("Dashed (--)", "--")
        self.cmb_linestyle.addItem("Dotted (:)", ":")
        self.cmb_linestyle.addItem("Dash-dot (-.)", "-.")
        form.addRow("Line style", self.cmb_linestyle)

        self.chk_enabled = QCheckBox("Enabled by default")
        form_container.addWidget(self.chk_enabled)

        # Actions
        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Add")
        self.btn_delete = QPushButton("Delete")
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_delete)
        btn_row.addStretch()
        form_container.addLayout(btn_row)

        self.btn_add.clicked.connect(self._add_model)
        self.btn_delete.clicked.connect(self._delete_model)

        # Dialog buttons
        bottom = QHBoxLayout()
        bottom.addStretch()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_save = QPushButton("Save")
        self.btn_save.setObjectName("primary")
        bottom.addWidget(self.btn_cancel)
        bottom.addWidget(self.btn_save)
        layout.addLayout(bottom)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._save_and_close)

    def _load_list(self):
        self.list_models.clear()
        ref_item = QListWidgetItem(self._reference_label)
        ref_item.setData(Qt.UserRole, self._reference_key)
        self.list_models.addItem(ref_item)
        for key in self.models.keys():
            item = QListWidgetItem(key)
            item.setData(Qt.UserRole, key)
            self.list_models.addItem(item)

        if self.list_models.count() > 1:
            self.list_models.setCurrentRow(1)
        elif self.list_models.count() > 0:
            self.list_models.setCurrentRow(0)
        else:
            self._set_form_enabled(False)

    def _set_form_enabled(self, enabled: bool):
        self.ed_label.setEnabled(enabled)
        self.sp_Om.setEnabled(enabled)
        self.sp_Ol.setEnabled(enabled)
        self.ed_color.setEnabled(enabled)
        self.btn_pick_color.setEnabled(enabled)
        self.cmb_linestyle.setEnabled(enabled)
        self.chk_enabled.setEnabled(enabled)
        self.btn_delete.setEnabled(enabled)
        self.ed_key.setEnabled(False)

    def _on_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        self._apply_current()
        if current is None:
            self._current_key = None
            self._set_form_enabled(False)
            return
        key = current.data(Qt.UserRole)
        self._current_key = key
        if key == self._reference_key:
            self._load_reference()
        else:
            self._load_current(key)

    def _load_current(self, key: str):
        model = self.models.get(key, {})
        self.ed_key.setText(key)
        self.ed_label.setText(model.get("label", key))
        self.sp_Om.setValue(float(model.get("Omega_m", 0.3)))
        self.sp_Ol.setValue(float(model.get("Omega_L", 0.7)))
        self.ed_color.setText(model.get("color", "#666666"))
        idx = self.cmb_linestyle.findData(model.get("linestyle", "-"))
        if idx >= 0:
            self.cmb_linestyle.setCurrentIndex(idx)
        self.chk_enabled.setChecked(bool(model.get("enabled", False)))
        self._set_form_enabled(True)

    def _apply_current(self):
        if self._current_key == self._reference_key:
            self._apply_reference()
            return
        if not self._current_key or self._current_key not in self.models:
            return
        self.models[self._current_key] = {
            "label": self.ed_label.text().strip() or self._current_key,
            "Omega_m": float(self.sp_Om.value()),
            "Omega_L": float(self.sp_Ol.value()),
            "color": self.ed_color.text().strip() or "#666666",
            "linestyle": self.cmb_linestyle.currentData(),
            "enabled": bool(self.chk_enabled.isChecked()),
        }

    def _add_model(self):
        if self._current_key == self._reference_key:
            self._current_key = None
            self._set_form_enabled(True)
        self._apply_current()
        key = self._generate_key("Custom")
        self.models[key] = {
            "label": key,
            "Omega_m": float(self.settings.Omega_m),
            "Omega_L": float(self.settings.Omega_L),
            "color": "#666666",
            "linestyle": "-",
            "enabled": False,
        }
        item = QListWidgetItem(key)
        item.setData(Qt.UserRole, key)
        self.list_models.addItem(item)
        self.list_models.setCurrentItem(item)

    def _delete_model(self):
        item = self.list_models.currentItem()
        if item is None:
            return
        key = item.data(Qt.UserRole)
        if key == self._reference_key:
            return
        reply = QMessageBox.question(
            self,
            "Delete Model",
            f"Delete model '{key}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.models.pop(key, None)
        row = self.list_models.row(item)
        self.list_models.takeItem(row)
        if self.list_models.count() > 0:
            self.list_models.setCurrentRow(min(row, self.list_models.count() - 1))
        else:
            self._current_key = None
            self._set_form_enabled(False)

    def _pick_color(self):
        current = self.ed_color.text().strip()
        color = QColorDialog.getColor()
        if color.isValid():
            self.ed_color.setText(color.name())
        elif current:
            self.ed_color.setText(current)

    def _generate_key(self, base: str) -> str:
        idx = 1
        key = f"{base}{idx}"
        while key in self.models:
            idx += 1
            key = f"{base}{idx}"
        return key

    def _save_and_close(self):
        self._apply_current()
        self.settings.set("models", value=self.models)
        self.accept()

    def _load_reference(self):
        self.ed_key.setText(self._reference_label)
        self.ed_label.setText(self._reference_label)
        self.sp_Om.setValue(float(self.settings.Omega_m))
        self.sp_Ol.setValue(float(self.settings.Omega_L))
        self.ed_color.setText(self._get_reference_color())
        idx = self.cmb_linestyle.findData(self._get_reference_linestyle())
        if idx >= 0:
            self.cmb_linestyle.setCurrentIndex(idx)
        self.chk_enabled.setChecked(True)
        self._set_reference_enabled()

    def _get_reference_color(self) -> str:
        color = self.settings.get("snia", "reference_color", default="")
        if color:
            return color
        theme = self.settings.theme
        return "#f0f0f0" if theme == "dark" else "#333333"

    def _get_reference_linestyle(self) -> str:
        return self.settings.get("snia", "reference_linestyle", default="-.")

    def _set_reference_enabled(self):
        self.ed_label.setEnabled(False)
        self.sp_Om.setEnabled(False)
        self.sp_Ol.setEnabled(False)
        self.ed_color.setEnabled(True)
        self.btn_pick_color.setEnabled(True)
        self.cmb_linestyle.setEnabled(True)
        self.chk_enabled.setEnabled(False)
        self.btn_delete.setEnabled(False)
        self.ed_key.setEnabled(False)

    def _apply_reference(self):
        self.settings.set(
            "snia", "reference_color", value=self.ed_color.text().strip()
        )
        self.settings.set(
            "snia", "reference_linestyle", value=self.cmb_linestyle.currentData()
        )
