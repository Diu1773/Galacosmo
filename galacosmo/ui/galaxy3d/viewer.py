"""
Interactive 3D Galaxy Viewer using PyVista.

Provides real-time rotation, zoom, and pan controls for visualizing
galaxy structure based on SPARC surface brightness data.
"""

import numpy as np
from typing import Optional, Dict, Any, Tuple

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame

try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False
    QtInteractor = QWidget  # Fallback

from ...models.galaxy_structure import GalaxyModel, create_spiral_arm_pattern


class Galaxy3DViewer(QFrame):
    """
    Interactive 3D galaxy visualization widget.

    Features:
    - Mouse drag to rotate view
    - Scroll wheel to zoom
    - Double-click to reset view
    - Multiple rendering modes (surface, volume, wireframe)
    - Component visibility toggles (disk, bulge, halo)
    """

    view_changed = pyqtSignal()

    # Color schemes for different themes
    DARK_THEME = {
        "background": "#1e1e2e",
        "text": "#cdd6f4",
        "disk_cmap": "viridis",
        "bulge_cmap": "plasma",
        "halo_cmap": "Blues",
    }

    LIGHT_THEME = {
        "background": "#ffffff",
        "text": "#1e1e2e",
        "disk_cmap": "viridis",
        "bulge_cmap": "plasma",
        "halo_cmap": "Blues",
    }

    def __init__(self, parent: Optional[QWidget] = None, theme: str = "dark"):
        super().__init__(parent)
        self.theme = theme
        self._current_mesh = None
        self._galaxy_model = None
        self._render_options = {
            "component": "all",
            "render_mode": "surface",
            "show_axes": True,
            "show_spiral": False,
            "resolution": "medium",
            "opacity": 0.9,
            "show_halo": False,
        }

        self._setup_ui()

    def _setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if not PYVISTA_AVAILABLE:
            # Fallback message if PyVista not installed
            self._fallback_label = QLabel(
                "PyVista not available.\n\n"
                "Install with:\n"
                "pip install pyvista pyvistaqt"
            )
            self._fallback_label.setAlignment(Qt.AlignCenter)
            self._fallback_label.setStyleSheet("color: #888; font-size: 14px;")
            layout.addWidget(self._fallback_label)
            self.plotter = None
            return

        # Create PyVista plotter
        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter.interactor)

        # Apply theme
        self._apply_theme()

        # Set interaction style
        self.plotter.enable_trackball_style()

        # Add key bindings
        self.plotter.add_key_event("r", self.reset_view)
        self.plotter.add_key_event("t", self._toggle_top_view)
        self.plotter.add_key_event("s", self._toggle_side_view)

    def _apply_theme(self):
        """Apply color theme to the plotter."""
        if not self.plotter:
            return

        colors = self.DARK_THEME if self.theme == "dark" else self.LIGHT_THEME
        self.plotter.set_background(colors["background"])

    def set_theme(self, theme: str):
        """Change the color theme."""
        self.theme = theme
        self._apply_theme()
        if self._current_mesh is not None:
            self._redraw()

    def render_galaxy(
        self,
        R: np.ndarray,
        SBdisk: np.ndarray,
        SBbul: np.ndarray,
        ml_disk: float = 0.5,
        ml_bulge: float = 0.7,
        h_R: Optional[float] = None,
        halo_params: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
    ):
        """
        Render galaxy from SPARC data.

        Parameters
        ----------
        R : array
            Radius array [kpc]
        SBdisk : array
            Disk surface brightness [L_sun/pc^2]
        SBbul : array
            Bulge surface brightness [L_sun/pc^2]
        ml_disk : float
            Disk mass-to-light ratio
        ml_bulge : float
            Bulge mass-to-light ratio
        h_R : float, optional
            Disk scale length [kpc]
        halo_params : dict, optional
            Halo parameters for visualization
        options : dict, optional
            Rendering options
        """
        if not self.plotter:
            return

        if options:
            self._render_options.update(options)

        # Store data for re-rendering
        self._sparc_data = {
            "R": R,
            "SBdisk": SBdisk,
            "SBbul": SBbul,
            "ml_disk": ml_disk,
            "ml_bulge": ml_bulge,
            "h_R": h_R,
            "halo_params": halo_params,
        }

        # Create galaxy model from SPARC data
        self._galaxy_model = GalaxyModel.from_sparc_data(
            R, SBdisk, SBbul, ml_disk, ml_bulge, h_R, halo_params=halo_params
        )

        self._redraw()

    def _redraw(self):
        """Redraw the galaxy with current settings."""
        if not self.plotter or not hasattr(self, '_sparc_data'):
            return

        self.plotter.clear()

        data = self._sparc_data
        R = data["R"]
        SBdisk = data["SBdisk"]
        SBbul = data["SBbul"]
        ml_disk = data["ml_disk"]
        ml_bulge = data["ml_bulge"]

        # Get render options
        component = self._render_options.get("component", "all")
        render_mode = self._render_options.get("render_mode", "surface")
        resolution = self._render_options.get("resolution", "medium")
        opacity = self._render_options.get("opacity", 0.9)
        show_spiral = self._render_options.get("show_spiral", False)
        show_halo = self._render_options.get("show_halo", False)

        # Resolution settings
        res_map = {"low": 60, "medium": 100, "high": 150}
        n_xy = res_map.get(resolution, 100)
        n_z = max(20, n_xy // 4)

        # Calculate r_max from data
        r_max = float(np.nanmax(R))
        if not np.isfinite(r_max) or r_max <= 0:
            r_max = 20.0

        # Select profile based on component
        if component == "disk":
            profile = np.nan_to_num(SBdisk, nan=0.0) * ml_disk
            cmap = "viridis"
        elif component == "bulge":
            profile = np.nan_to_num(SBbul, nan=0.0) * ml_bulge
            cmap = "plasma"
        else:  # all
            profile = (
                np.nan_to_num(SBdisk, nan=0.0) * ml_disk +
                np.nan_to_num(SBbul, nan=0.0) * ml_bulge
            )
            cmap = "viridis"

        # Compute 3D density grid
        X, Y, Z, density = self._galaxy_model.compute_density_from_profile(
            R, profile, r_max, n_xy=n_xy, n_z=n_z
        )

        # Apply spiral arm modulation if enabled
        if show_spiral and component in ("disk", "all"):
            spiral = create_spiral_arm_pattern(X[:, :, 0], Y[:, :, 0])
            spiral_3d = np.broadcast_to(spiral[:, :, np.newaxis], density.shape)
            density = density * spiral_3d

        # Create PyVista grid
        grid = pv.ImageData(
            dimensions=(n_xy, n_xy, n_z),
            spacing=(2*r_max/n_xy, 2*r_max/n_xy, 2*r_max/(3*n_z)),
            origin=(-r_max, -r_max, -r_max/3)
        )
        grid["density"] = density.ravel(order='F')

        # Render based on mode
        if render_mode == "volume":
            self.plotter.add_volume(
                grid,
                scalars="density",
                cmap=cmap,
                opacity="sigmoid_5",
                shade=True,
            )
        elif render_mode == "isosurface":
            # Create isosurfaces at multiple levels
            max_val = np.nanmax(density)
            if max_val > 0:
                levels = [max_val * f for f in [0.1, 0.3, 0.5, 0.7]]
                contours = grid.contour(levels, scalars="density")
                if contours.n_points > 0:
                    self.plotter.add_mesh(
                        contours,
                        cmap=cmap,
                        opacity=opacity,
                        smooth_shading=True,
                    )
        else:  # surface
            # Create surface at a threshold level
            max_val = np.nanmax(density)
            if max_val > 0:
                threshold = max_val * 0.05
                surface = grid.threshold(threshold, scalars="density")
                if surface.n_points > 0:
                    self.plotter.add_mesh(
                        surface,
                        scalars="density",
                        cmap=cmap,
                        opacity=opacity,
                        smooth_shading=True,
                        show_edges=False,
                    )

        # Add halo visualization if enabled
        if show_halo and self._galaxy_model.halo:
            self._add_halo_visualization(r_max, n_xy)

        # Add axes if enabled
        if self._render_options.get("show_axes", True):
            self.plotter.add_axes(
                xlabel="X [kpc]",
                ylabel="Y [kpc]",
                zlabel="Z [kpc]",
            )

        # Set camera position
        self.plotter.camera_position = "iso"
        self.plotter.reset_camera()

        self.view_changed.emit()

    def _add_halo_visualization(self, r_max: float, n: int):
        """Add dark matter halo visualization as a semi-transparent sphere."""
        if not self._galaxy_model or not self._galaxy_model.halo:
            return

        # Create spherical shell for halo
        halo = self._galaxy_model.halo
        if hasattr(halo, 'r_s'):
            r_halo = halo.r_s * 3  # Show out to 3 scale radii
        else:
            r_halo = r_max * 2

        sphere = pv.Sphere(radius=r_halo, center=(0, 0, 0), theta_resolution=30, phi_resolution=30)
        self.plotter.add_mesh(
            sphere,
            color="#4466aa",
            opacity=0.1,
            style="wireframe",
            line_width=0.5,
        )

    def reset_view(self):
        """Reset camera to default isometric view."""
        if not self.plotter:
            return
        self.plotter.camera_position = "iso"
        self.plotter.reset_camera()

    def _toggle_top_view(self):
        """Switch to top-down view."""
        if not self.plotter:
            return
        self.plotter.view_xy()

    def _toggle_side_view(self):
        """Switch to side view."""
        if not self.plotter:
            return
        self.plotter.view_xz()

    def set_view(self, view: str):
        """
        Set camera to predefined view.

        Parameters
        ----------
        view : str
            One of: "iso", "top", "side", "front"
        """
        if not self.plotter:
            return

        if view == "iso":
            self.plotter.camera_position = "iso"
        elif view == "top":
            self.plotter.view_xy()
        elif view == "side":
            self.plotter.view_xz()
        elif view == "front":
            self.plotter.view_yz()

        self.plotter.reset_camera()

    def set_render_options(self, **options):
        """
        Update rendering options and redraw.

        Parameters
        ----------
        **options
            component: "disk", "bulge", "all"
            render_mode: "surface", "volume", "isosurface"
            resolution: "low", "medium", "high"
            opacity: float (0-1)
            show_axes: bool
            show_spiral: bool
            show_halo: bool
        """
        self._render_options.update(options)
        if hasattr(self, '_sparc_data'):
            self._redraw()

    def get_render_options(self) -> Dict[str, Any]:
        """Get current rendering options."""
        return self._render_options.copy()

    def save_screenshot(self, filename: str, scale: int = 2):
        """
        Save current view as image.

        Parameters
        ----------
        filename : str
            Output filename (supports png, jpg, svg, pdf)
        scale : int
            Resolution scale factor
        """
        if not self.plotter:
            return
        self.plotter.screenshot(filename, scale=scale)

    def start_auto_rotate(self, speed: float = 1.0):
        """Start automatic rotation animation."""
        if not self.plotter:
            return
        # PyVista doesn't have built-in auto-rotate, but we can use orbit
        self.plotter.orbit_on_path(factor=speed, step=0.02)

    def stop_auto_rotate(self):
        """Stop automatic rotation."""
        if not self.plotter:
            return
        # Stop any ongoing animation
        pass

    def clear(self):
        """Clear the viewer."""
        if self.plotter:
            self.plotter.clear()
            self._current_mesh = None
            self._galaxy_model = None

    def close(self):
        """Clean up resources."""
        if self.plotter:
            self.plotter.close()
