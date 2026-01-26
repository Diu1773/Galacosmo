"""Optimized Matplotlib canvas widget for PyQt5."""

import numpy as np
from typing import Optional, Callable

import matplotlib
matplotlib.use("Qt5Agg")

from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from mpl_toolkits.mplot3d import Axes3D  # Registers 3D projection.

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox


class PlotCanvas(QWidget):
    """
    Optimized matplotlib canvas with toolbar.

    Features:
    - Automatic theme integration
    - Optimized redrawing
    - Easy subplot management
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        figsize: tuple = (8, 6),
        dpi: int = 100,
        tight_layout: bool = True,
        projection: Optional[str] = None,
    ):
        super().__init__(parent)

        self._help_text = ""
        self._help_callback = None
        self._projection = projection

        self._setup_figure(figsize, dpi, tight_layout)
        self._setup_layout()
        self._redraw_pending = False

    def _setup_figure(self, figsize: tuple, dpi: int, tight_layout: bool):
        """Initialize matplotlib figure."""
        self.figure = Figure(figsize=figsize, dpi=dpi)
        if tight_layout:
            self.figure.set_tight_layout(True)

        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)

        # Create default axes
        if self._projection:
            self.ax = self.figure.add_subplot(111, projection=self._projection)
        else:
            self.ax = self.figure.add_subplot(111)

    def _setup_layout(self):
        """Setup widget layout."""
        if not hasattr(self, "_help_text"):
            self._help_text = ""
        if not hasattr(self, "_help_callback"):
            self._help_callback = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, stretch=1)
        self._add_help_action()

    def _add_help_action(self):
        """Add a help action to the toolbar."""
        self.toolbar.addAction("?", self._on_help_clicked)

    def _on_help_clicked(self):
        """Show help text or call a help callback."""
        if callable(self._help_callback):
            self._help_callback()
            return
        if self._help_text:
            QMessageBox.information(self, "Help", self._help_text)
            return
        QMessageBox.information(self, "Help", "No help available for this view.")

    def set_help_text(self, text: str):
        """Set help text for the toolbar help action."""
        self._help_text = text or ""

    def set_help_callback(self, callback: Optional[Callable[[], None]]):
        """Set a callback for the toolbar help action."""
        self._help_callback = callback

    def add_subplot(self, *args, **kwargs):
        """Add a subplot to the figure."""
        return self.figure.add_subplot(*args, **kwargs)

    def clear(self):
        """Clear all axes."""
        for ax in self.figure.axes:
            ax.clear()

    def draw(self):
        """Redraw the canvas."""
        self.canvas.draw()

    def draw_idle(self):
        """Schedule a redraw when idle."""
        self.canvas.draw_idle()

    def save_figure(self, path: str, **kwargs):
        """Save figure to file."""
        self.figure.savefig(path, **kwargs)

    def apply_theme_colors(self, theme: str = "dark"):
        """Apply theme-appropriate colors to axes."""
        if theme == "dark":
            bg_color = "#1e1e2e"
            fg_color = "#cdd6f4"
            grid_color = "#45475a"
        else:
            bg_color = "#ffffff"
            fg_color = "#1e1e2e"
            grid_color = "#e0e0e0"

        self.figure.set_facecolor(bg_color)

        for ax in self.figure.axes:
            ax.set_facecolor(bg_color)
            ax.tick_params(colors=fg_color)
            ax.xaxis.label.set_color(fg_color)
            ax.yaxis.label.set_color(fg_color)
            ax.title.set_color(fg_color)
            if hasattr(ax, "zaxis"):
                ax.zaxis.label.set_color(fg_color)
                ax.tick_params(axis="z", colors=fg_color)

            for spine in ax.spines.values():
                spine.set_color(grid_color)


class DualPanelCanvas(PlotCanvas):
    """
    Canvas with two vertically stacked panels sharing x-axis.
    Commonly used for Hubble diagram (main + residuals).
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        figsize: tuple = (10, 8),
        height_ratios: tuple = (3, 1),
        **kwargs,
    ):
        # Don't call parent __init__ yet
        QWidget.__init__(self, parent)
        self._help_text = ""
        self._help_callback = None

        self._setup_dual_figure(figsize, height_ratios, kwargs.get("dpi", 100))
        self._setup_layout()

    def _setup_dual_figure(self, figsize: tuple, height_ratios: tuple, dpi: int):
        """Initialize dual-panel figure."""
        self.figure = Figure(figsize=figsize, dpi=dpi)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)

        # Create gridspec for height ratio control
        gs = self.figure.add_gridspec(
            2, 1,
            height_ratios=height_ratios,
            hspace=0.05,
        )

        self.ax_main = self.figure.add_subplot(gs[0])
        self.ax_residual = self.figure.add_subplot(gs[1], sharex=self.ax_main)

        # Hide x-axis labels on main panel
        self.ax_main.tick_params(labelbottom=False)

        # Reference for compatibility
        self.ax = self.ax_main
        self._main_pos = self.ax_main.get_position()
        self._res_pos = self.ax_residual.get_position()
        self._full_pos = Bbox.from_extents(
            min(self._main_pos.x0, self._res_pos.x0),
            min(self._main_pos.y0, self._res_pos.y0),
            max(self._main_pos.x1, self._res_pos.x1),
            max(self._main_pos.y1, self._res_pos.y1),
        )
        self._residuals_visible = True

    def clear(self):
        """Clear both panels."""
        self.ax_main.clear()
        self.ax_residual.clear()
        # Re-hide x labels after clear
        self.ax_main.tick_params(labelbottom=False)

    def set_residuals_visible(self, visible: bool):
        """Show or hide the residual panel."""
        if self._residuals_visible == visible:
            return

        self._residuals_visible = visible

        if visible:
            self.ax_residual.set_visible(True)
            self.ax_main.set_position(self._main_pos)
            self.ax_residual.set_position(self._res_pos)
            self.ax_main.tick_params(labelbottom=False)
        else:
            self.ax_residual.set_visible(False)
            self.ax_main.set_position(self._full_pos)
            self.ax_main.tick_params(labelbottom=True)


class FastScatterCanvas(PlotCanvas):
    """
    Canvas optimized for large scatter plots.
    Uses techniques like:
    - Reduced marker complexity
    - Alpha blending for density
    - Automatic downsampling hints
    """

    def scatter_fast(
        self,
        x: np.ndarray,
        y: np.ndarray,
        color: str = "#377eb8",
        size: float = 4,
        alpha: float = 0.7,
        label: Optional[str] = None,
        ax=None,
    ):
        """
        Fast scatter plot for large datasets.

        Uses plot() with markers instead of scatter() for speed.
        """
        if ax is None:
            ax = self.ax

        n_points = len(x)

        # Adjust visual parameters based on point count
        if n_points > 2000:
            size = max(1, size * 0.5)
            alpha = max(0.3, alpha * 0.6)
        elif n_points > 500:
            size = max(2, size * 0.7)
            alpha = max(0.5, alpha * 0.8)

        # Use plot instead of scatter (faster)
        ax.plot(
            x, y, "o",
            markersize=size,
            color=color,
            alpha=alpha,
            markeredgewidth=0,
            label=label,
            zorder=2,
        )

    def errorbar_fast(
        self,
        x: np.ndarray,
        y: np.ndarray,
        yerr: Optional[np.ndarray] = None,
        color: str = "#377eb8",
        size: float = 4,
        alpha: float = 0.7,
        label: Optional[str] = None,
        ax=None,
        use_fill: bool = False,
    ):
        """
        Fast error bar plot.

        For large datasets, can use fill_between instead of errorbar.
        """
        if ax is None:
            ax = self.ax

        n_points = len(x)

        if yerr is not None and use_fill and n_points > 500:
            # Use fill_between for large datasets (faster)
            sort_idx = np.argsort(x)
            x_sorted = x[sort_idx]
            y_sorted = y[sort_idx]
            yerr_sorted = yerr[sort_idx]

            ax.fill_between(
                x_sorted,
                y_sorted - yerr_sorted,
                y_sorted + yerr_sorted,
                alpha=alpha * 0.3,
                color=color,
                linewidth=0,
            )
            self.scatter_fast(x, y, color, size, alpha, label, ax)
        else:
            # Regular errorbar for smaller datasets
            if n_points > 1000:
                capsize = 0
                elinewidth = 0.3
            else:
                capsize = 2
                elinewidth = 0.5

            ax.errorbar(
                x, y,
                yerr=yerr,
                fmt="o",
                markersize=size,
                color=color,
                alpha=alpha,
                capsize=capsize,
                elinewidth=elinewidth,
                markeredgewidth=0,
                label=label,
                zorder=2,
            )
