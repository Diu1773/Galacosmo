"""Main window for GalaCosmo application."""

import os
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSizePolicy,
)
from PyQt5.QtGui import QIcon, QFont

from ..config import get_settings
from .styles import get_theme_manager
from .dialogs import SettingsDialog, GuideDialog


class CardWidget(QFrame):
    """Clickable card widget for main menu."""

    def __init__(
        self,
        title: str,
        description: str,
        icon_text: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Icon/emoji
        if icon_text:
            icon_label = QLabel(icon_text)
            icon_label.setFont(QFont("Segoe UI Emoji", 32))
            icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(description)
        desc_label.setObjectName("subtitle")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        self._callback = None

    def set_callback(self, callback):
        """Set click callback."""
        self._callback = callback

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._callback:
            self._callback()
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    """Main application window with card-based menu."""

    def __init__(self, app_icon=None):
        super().__init__()
        self.app_icon = app_icon
        self._rotation_window = None
        self._hubble_window = None

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        self.setWindowTitle("GalaCosmo")
        self.setMinimumSize(600, 500)
        self.resize(700, 550)

        if self.app_icon:
            self.setWindowIcon(self.app_icon)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)

        title = QLabel("GalaCosmo")
        title.setObjectName("title")
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)

        subtitle = QLabel("예비교사를 위한 OER 기반 암흑물질·우주론 탐구 GUI")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(20)

        # Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        # Rotation curve card
        self.card_rotation = CardWidget(
            title="은하 회전곡선",
            description="SPARC 실제 데이터로\n암흑물질 필요성을 탐구",
            icon_text="\U0001F300",  # Galaxy emoji
        )
        self.card_rotation.set_callback(self._open_rotation)
        cards_layout.addWidget(self.card_rotation)

        # Hubble diagram card
        self.card_hubble = CardWidget(
            title="허블 다이어그램",
            description="확장 활동: SN Ia 데이터로\n우주론 모형 비교",
            icon_text="\U00002B50",  # Star emoji
        )
        self.card_hubble.set_callback(self._open_hubble)
        cards_layout.addWidget(self.card_hubble)

        main_layout.addLayout(cards_layout)
        main_layout.addStretch()

        # Footer with settings button
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()

        self.btn_guide = QPushButton("예비교사 가이드")
        self.btn_guide.clicked.connect(self._open_guide)
        footer_layout.addWidget(self.btn_guide)

        self.btn_settings = QPushButton("설정")
        self.btn_settings.clicked.connect(self._open_settings)
        footer_layout.addWidget(self.btn_settings)

        main_layout.addLayout(footer_layout)

    def _apply_theme(self):
        """Apply current theme."""
        # Theme is applied at app level in app.py
        get_settings()

    def _open_rotation(self):
        """Open rotation curve window."""
        if self._rotation_window is None:
            from .rotation import RotationCurveWindow
            self._rotation_window = RotationCurveWindow(
                parent=self, app_icon=self.app_icon
            )
        self._rotation_window.show()
        self._rotation_window.raise_()
        self._rotation_window.activateWindow()

    def _open_hubble(self):
        """Open Hubble diagram window."""
        if self._hubble_window is None:
            from .hubble import HubbleDiagramWindow
            self._hubble_window = HubbleDiagramWindow(
                parent=self, app_icon=self.app_icon
            )
        self._hubble_window.show()
        self._hubble_window.raise_()
        self._hubble_window.activateWindow()

    def _open_settings(self):
        """Open settings dialog."""
        dialog = SettingsDialog(self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec_()

    def _open_guide(self):
        """Open guide dialog."""
        dialog = GuideDialog(self)
        dialog.exec_()

    def _on_settings_changed(self):
        """Handle settings changes."""
        settings = get_settings()

        # Apply theme if changed
        from .styles import get_theme_manager
        theme_manager = get_theme_manager()
        theme_manager.apply_theme(settings.theme)

        # Notify child windows
        if self._rotation_window:
            self._rotation_window.on_settings_changed()
        if self._hubble_window:
            self._hubble_window.on_settings_changed()
