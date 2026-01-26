"""Color palettes and visual styles for GalaCosmo."""

# ColorBrewer qualitative palette (colorblind-friendly)
PALETTE_QUALITATIVE = [
    "#e41a1c",  # Red
    "#377eb8",  # Blue
    "#4daf4a",  # Green
    "#984ea3",  # Purple
    "#ff7f00",  # Orange
    "#a65628",  # Brown
    "#f781bf",  # Pink
    "#999999",  # Gray
    "#66c2a5",  # Teal
    "#fc8d62",  # Coral
]

# High contrast palette
PALETTE_HIGH_CONTRAST = [
    "#000000",  # Black
    "#e41a1c",  # Red
    "#377eb8",  # Blue
    "#4daf4a",  # Green
    "#984ea3",  # Purple
    "#ff7f00",  # Orange
    "#ffff33",  # Yellow
    "#a65628",  # Brown
    "#f781bf",  # Pink
    "#999999",  # Gray
]

# Default (original) palette
PALETTE_DEFAULT = [
    "#000000",  # Black
    "#ff7f0e",  # Orange
    "#2ca02c",  # Green
    "#d62728",  # Red
    "#9467bd",  # Purple
    "#791818",  # Dark red
    "#e377c2",  # Pink
    "#7f7f7f",  # Gray
    "#bcbd22",  # Olive
    "#17becf",  # Cyan
]

# Palette mapping
PALETTES = {
    "colorbrewer": PALETTE_QUALITATIVE,
    "high_contrast": PALETTE_HIGH_CONTRAST,
    "default": PALETTE_DEFAULT,
}

# Distinct markers for data points
MARKERS_DISTINCT = [
    "o",  # Circle
    "s",  # Square
    "^",  # Triangle up
    "D",  # Diamond
    "v",  # Triangle down
    "p",  # Pentagon
    "h",  # Hexagon
    "*",  # Star
    "X",  # X marker
    "P",  # Plus (filled)
]

# Rotation curve component colors
ROTATION_COLORS = {
    "Observed": "#000000",
    "Disk": "#1f77b4",
    "Bulge": "#9467bd",
    "Gas": "#2ca02c",
    "Baryons": "#ff7f0e",
    "Halo": "#d62728",
    "Total": "#111111",
}

# Cosmology model line styles
COSMO_LINE_STYLES = {
    "solid": "-",
    "dashed": "--",
    "dotted": ":",
    "dashdot": "-.",
}

# Default cosmology model visual styles
DEFAULT_COSMO_STYLES = {
    "LCDM": {
        "label": "LCDM",
        "Omega_m": 0.315,
        "Omega_L": 0.685,
        "color": "#377eb8",
        "linestyle": "-",
    },
    "Open": {
        "label": "Open",
        "Omega_m": 0.315,
        "Omega_L": 0.0,
        "color": "#4daf4a",
        "linestyle": "--",
    },
    "EdS": {
        "label": "EdS",
        "Omega_m": 1.0,
        "Omega_L": 0.0,
        "color": "#e41a1c",
        "linestyle": ":",
    },
}


class DataStyler:
    """Automatically assigns distinct colors and markers to datasets."""

    def __init__(self, palette_name: str = "colorbrewer"):
        self.palette = PALETTES.get(palette_name, PALETTE_QUALITATIVE)
        self.markers = MARKERS_DISTINCT
        self._color_idx = 0
        self._marker_idx = 0

    def reset(self):
        """Reset style assignment counters."""
        self._color_idx = 0
        self._marker_idx = 0

    def next_style(self) -> dict:
        """Get next unique style combination."""
        color = self.palette[self._color_idx % len(self.palette)]
        marker = self.markers[self._color_idx // len(self.palette) % len(self.markers)]
        self._color_idx += 1
        return {
            "color": color,
            "marker": marker,
            "edgecolor": "white",
            "linewidth": 0.5,
        }

    def get_style(self, index: int) -> dict:
        """Get style for a specific index."""
        color = self.palette[index % len(self.palette)]
        marker = self.markers[index // len(self.palette) % len(self.markers)]
        return {
            "color": color,
            "marker": marker,
            "edgecolor": "white",
            "linewidth": 0.5,
        }
