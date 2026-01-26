"""Theme management for GalaCosmo UI."""

import sys
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import QApplication


def _get_styles_dir() -> Path:
    """Get styles directory, works for both dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / 'galacosmo' / 'ui' / 'styles'
    return Path(__file__).parent


STYLES_DIR = _get_styles_dir()


def load_stylesheet(theme: str = "dark") -> str:
    """
    Load a theme stylesheet.

    Parameters
    ----------
    theme : str
        Theme name ("dark" or "light")

    Returns
    -------
    str
        QSS stylesheet content
    """
    filename = f"{theme}.qss"
    path = STYLES_DIR / filename

    if not path.exists():
        path = STYLES_DIR / "dark.qss"

    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


class ThemeManager:
    """Manages application theming."""

    def __init__(self, app: Optional[QApplication] = None):
        self._app = app
        self._current_theme = "dark"
        self._stylesheet_cache = {}

    def set_app(self, app: QApplication):
        """Set the application instance."""
        self._app = app

    @property
    def current_theme(self) -> str:
        """Get current theme name."""
        return self._current_theme

    def apply_theme(self, theme: str = "dark"):
        """
        Apply a theme to the application.

        Parameters
        ----------
        theme : str
            Theme name ("dark" or "light")
        """
        if self._app is None:
            return

        if theme not in self._stylesheet_cache:
            self._stylesheet_cache[theme] = load_stylesheet(theme)

        self._app.setStyleSheet(self._stylesheet_cache[theme])
        self._current_theme = theme

        # Also update matplotlib style
        self._apply_matplotlib_theme(theme)

    def _apply_matplotlib_theme(self, theme: str):
        """Apply matching matplotlib style."""
        import matplotlib.pyplot as plt

        if theme == "dark":
            plt.style.use("dark_background")
            # Customize for better integration
            plt.rcParams.update({
                "figure.facecolor": "#1e1e2e",
                "axes.facecolor": "#313244",
                "axes.edgecolor": "#45475a",
                "axes.labelcolor": "#cdd6f4",
                "text.color": "#cdd6f4",
                "xtick.color": "#cdd6f4",
                "ytick.color": "#cdd6f4",
                "grid.color": "#45475a",
                "legend.facecolor": "#313244",
                "legend.edgecolor": "#45475a",
            })
        else:
            plt.style.use("default")
            plt.rcParams.update({
                "figure.facecolor": "#ffffff",
                "axes.facecolor": "#ffffff",
                "axes.edgecolor": "#d0d0d0",
                "axes.labelcolor": "#1e1e2e",
                "text.color": "#1e1e2e",
                "xtick.color": "#1e1e2e",
                "ytick.color": "#1e1e2e",
                "grid.color": "#e0e0e0",
            })

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self.apply_theme(new_theme)
        return new_theme

    def get_plot_colors(self) -> dict:
        """Get colors suitable for current theme."""
        if self._current_theme == "dark":
            return {
                "background": "#1e1e2e",
                "foreground": "#cdd6f4",
                "grid": "#45475a",
                "accent": "#7c3aed",
            }
        else:
            return {
                "background": "#ffffff",
                "foreground": "#1e1e2e",
                "grid": "#e0e0e0",
                "accent": "#7c3aed",
            }


# Global theme manager instance
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def apply_theme(theme: str = "dark"):
    """Convenience function to apply a theme."""
    get_theme_manager().apply_theme(theme)
