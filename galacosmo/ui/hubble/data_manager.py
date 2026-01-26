"""Dataset manager for Hubble diagram."""

from typing import Dict, List, Optional, Tuple
import pandas as pd

from ...config.palettes import DataStyler


class DatasetManager:
    """Manages multiple SN Ia datasets with styling."""

    def __init__(self, palette_name: str = "colorbrewer"):
        self.datasets: Dict[str, dict] = {}
        self.styler = DataStyler(palette_name)

    def add_dataset(
        self,
        label: str,
        df: pd.DataFrame,
        enabled: bool = False,
    ) -> str:
        """
        Add a dataset.

        Parameters
        ----------
        label : str
            Dataset label
        df : DataFrame
            Data with columns: z, mu, emu
        enabled : bool
            Whether to display by default

        Returns
        -------
        str
            The actual label used (may be modified if duplicate)
        """
        # Handle duplicate labels
        if label in self.datasets:
            base = label
            k = 2
            while label in self.datasets:
                label = f"{base} ({k})"
                k += 1

        # Assign style
        style = self.styler.next_style()

        self.datasets[label] = {
            "df": df,
            "enabled": enabled,
            "color": style["color"],
            "marker": style["marker"],
        }

        return label

    def remove_dataset(self, label: str):
        """Remove a dataset."""
        if label in self.datasets:
            del self.datasets[label]

    def clear(self):
        """Remove all datasets."""
        self.datasets.clear()
        self.styler.reset()

    def set_enabled(self, label: str, enabled: bool):
        """Enable or disable a dataset."""
        if label in self.datasets:
            self.datasets[label]["enabled"] = enabled

    def get_enabled_datasets(self) -> List[Tuple[str, dict]]:
        """Get list of enabled datasets with their metadata."""
        return [
            (label, data)
            for label, data in self.datasets.items()
            if data.get("enabled", False)
        ]

    def get_all_labels(self) -> List[str]:
        """Get all dataset labels."""
        return list(self.datasets.keys())

    def get_dataset(self, label: str) -> Optional[dict]:
        """Get dataset by label."""
        return self.datasets.get(label)

    def get_total_points(self, enabled_only: bool = True) -> int:
        """Get total number of data points."""
        if enabled_only:
            return sum(
                len(data["df"])
                for data in self.datasets.values()
                if data.get("enabled", False)
            )
        return sum(len(data["df"]) for data in self.datasets.values())

    def set_palette(self, palette_name: str):
        """Change color palette and reassign colors."""
        self.styler = DataStyler(palette_name)

        # Reassign styles
        for label in self.datasets:
            style = self.styler.next_style()
            self.datasets[label]["color"] = style["color"]
            self.datasets[label]["marker"] = style["marker"]

    def set_color(self, label: str, color: str):
        """Set a custom color for a dataset."""
        if label in self.datasets:
            self.datasets[label]["color"] = color

    def __len__(self) -> int:
        return len(self.datasets)

    def __iter__(self):
        return iter(self.datasets.items())
