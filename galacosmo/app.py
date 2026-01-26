"""Main application entry point for GalaCosmo."""

import sys
import os
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from .config import get_settings
from .ui.styles import get_theme_manager, load_stylesheet
from .ui import MainWindow


def create_icon() -> QIcon:
    """Create or load application icon."""
    # Check for icon in resources
    resources_dir = Path(__file__).parent / "resources" / "icons"
    icon_path = resources_dir / "logo.svg"

    if icon_path.exists():
        return QIcon(str(icon_path))

    # Generate default icon
    svg_content = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="g1" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#1e1e2e"/>
      <stop offset="80%" stop-color="#1e1e2e"/>
      <stop offset="100%" stop-color="#11111b"/>
    </radialGradient>
    <linearGradient id="g2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#7c3aed"/>
      <stop offset="100%" stop-color="#a855f7"/>
    </linearGradient>
  </defs>
  <!-- Background -->
  <circle cx="256" cy="256" r="240" fill="url(#g1)" stroke="#45475a" stroke-width="4"/>
  <!-- Galaxy spiral -->
  <ellipse cx="256" cy="256" rx="200" ry="100" fill="none" stroke="url(#g2)"
           stroke-width="12" opacity="0.9" transform="rotate(-15 256 256)"/>
  <ellipse cx="256" cy="256" rx="150" ry="70" fill="none" stroke="#9333ea"
           stroke-width="8" opacity="0.7" transform="rotate(-15 256 256)"/>
  <ellipse cx="256" cy="256" rx="100" ry="45" fill="none" stroke="#a855f7"
           stroke-width="6" opacity="0.5" transform="rotate(-15 256 256)"/>
  <!-- Core -->
  <circle cx="256" cy="256" r="30" fill="#ffffff" opacity="0.95"/>
  <circle cx="256" cy="256" r="20" fill="#7c3aed" opacity="0.8"/>
  <!-- Stars -->
  <circle cx="120" cy="150" r="3" fill="#fff" opacity="0.8"/>
  <circle cx="380" cy="130" r="4" fill="#fff" opacity="0.7"/>
  <circle cx="400" cy="300" r="3" fill="#fff" opacity="0.6"/>
  <circle cx="100" cy="350" r="3" fill="#fff" opacity="0.7"/>
  <circle cx="300" cy="400" r="3" fill="#fff" opacity="0.6"/>
  <circle cx="180" cy="420" r="2" fill="#fff" opacity="0.5"/>
</svg>'''

    # Try to write into package resources (may be read-only when installed)
    try:
        resources_dir.mkdir(parents=True, exist_ok=True)
        with open(icon_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        return QIcon(str(icon_path))
    except OSError:
        pass

    # Fall back to a user-writable location
    try:
        from .config.settings import CONFIG_DIR
        user_dir = CONFIG_DIR / "icons"
    except Exception:
        if os.name == "nt":
            user_dir = Path(os.environ.get("APPDATA", "")) / "GalaCosmo" / "icons"
        else:
            user_dir = Path.home() / ".config" / "galacosmo" / "icons"

    try:
        user_dir.mkdir(parents=True, exist_ok=True)
        user_icon_path = user_dir / "logo.svg"
        with open(user_icon_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        return QIcon(str(user_icon_path))
    except OSError:
        return QIcon()


def main():
    """Main entry point."""
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("GalaCosmo")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("GalaCosmo")

    # Load settings
    settings = get_settings()

    # Create and set icon
    app_icon = create_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    # Apply theme
    theme_manager = get_theme_manager()
    theme_manager.set_app(app)
    stylesheet = load_stylesheet(settings.theme)
    app.setStyleSheet(stylesheet)
    theme_manager.apply_theme(settings.theme)

    # Create main window
    window = MainWindow(app_icon=app_icon)
    window.show()

    # Run event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
