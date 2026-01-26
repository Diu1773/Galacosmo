"""Appearance settings dialog for GalaCosmo."""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QDoubleSpinBox,
    QComboBox, QGroupBox, QTabWidget,
    QWidget,
)

from ...config import get_settings


class SettingsDialog(QDialog):
    """Settings dialog for appearance options."""

    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = get_settings()
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 600)

        layout = QVBoxLayout(self)

        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._create_appearance_tab()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_reset = QPushButton("Reset Appearance")
        self.btn_reset.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(self.btn_reset)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Save")
        self.btn_save.setObjectName("primary")
        self.btn_save.clicked.connect(self._save_and_close)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def _create_appearance_tab(self):
        """Create appearance settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Theme
        theme_group = QGroupBox("Theme")
        theme_layout = QHBoxLayout(theme_group)

        theme_layout.addWidget(QLabel("Color theme:"))
        self.cmb_theme = QComboBox()
        self.cmb_theme.addItem("Dark", "dark")
        self.cmb_theme.addItem("Light", "light")
        theme_layout.addWidget(self.cmb_theme)
        theme_layout.addStretch()

        layout.addWidget(theme_group)

        # Palette
        palette_group = QGroupBox("Color Palette")
        palette_layout = QHBoxLayout(palette_group)

        palette_layout.addWidget(QLabel("Data colors:"))
        self.cmb_palette = QComboBox()
        self.cmb_palette.addItem("ColorBrewer (colorblind-friendly)", "colorbrewer")
        self.cmb_palette.addItem("High Contrast", "high_contrast")
        self.cmb_palette.addItem("Default", "default")
        palette_layout.addWidget(self.cmb_palette)
        palette_layout.addStretch()

        layout.addWidget(palette_group)

        # Plot style
        plot_group = QGroupBox("Plot Style")
        plot_layout = QGridLayout(plot_group)

        plot_layout.addWidget(QLabel("Marker size:"), 0, 0)
        self.sp_marker_size = QDoubleSpinBox()
        self.sp_marker_size.setRange(1, 20)
        self.sp_marker_size.setDecimals(1)
        plot_layout.addWidget(self.sp_marker_size, 0, 1)

        plot_layout.addWidget(QLabel("Line width:"), 1, 0)
        self.sp_line_width = QDoubleSpinBox()
        self.sp_line_width.setRange(0.5, 5)
        self.sp_line_width.setDecimals(1)
        plot_layout.addWidget(self.sp_line_width, 1, 1)

        layout.addWidget(plot_group)
        layout.addStretch()

        self.tabs.addTab(widget, "Appearance")

    def _load_values(self):
        """Load current settings into UI."""
        s = self.settings

        # Appearance
        idx = self.cmb_theme.findData(s.theme)
        if idx >= 0:
            self.cmb_theme.setCurrentIndex(idx)
        idx = self.cmb_palette.findData(s.palette)
        if idx >= 0:
            self.cmb_palette.setCurrentIndex(idx)
        self.sp_marker_size.setValue(s.get("appearance", "marker_size", default=4))
        self.sp_line_width.setValue(s.get("appearance", "line_width", default=1.5))

    def _save_values(self):
        """Save UI values to settings."""
        s = self.settings

        # Appearance
        s.theme = self.cmb_theme.currentData()
        s.palette = self.cmb_palette.currentData()
        s.set("appearance", "marker_size", value=self.sp_marker_size.value())
        s.set("appearance", "line_width", value=self.sp_line_width.value())

    def _reset_defaults(self):
        """Reset appearance settings to defaults."""
        default_theme = "dark"
        default_palette = "colorbrewer"
        default_marker_size = 4
        default_line_width = 1.5

        self.settings.theme = default_theme
        self.settings.palette = default_palette
        self.settings.set("appearance", "marker_size", value=default_marker_size)
        self.settings.set("appearance", "line_width", value=default_line_width)
        self._load_values()

    def _save_and_close(self):
        """Save settings and close dialog."""
        self._save_values()
        self.settings_changed.emit()
        self.accept()
