"""Settings management with TOML persistence."""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import toml

# Default config directory
if os.name == 'nt':  # Windows
    CONFIG_DIR = Path(os.environ.get('APPDATA', '')) / 'GalaCosmo'
else:  # Linux/Mac
    CONFIG_DIR = Path.home() / '.config' / 'galacosmo'

CONFIG_FILE = CONFIG_DIR / 'settings.toml'


def _get_default_settings_path() -> Path:
    """Get default settings path, works for both dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / 'galacosmo' / 'config' / 'default_settings.toml'
    return Path(__file__).parent / 'default_settings.toml'


DEFAULT_SETTINGS_PATH = _get_default_settings_path()


def _deep_update(base: dict, update: dict) -> dict:
    """Recursively update a nested dictionary."""
    result = base.copy()
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_update(result[key], value)
        else:
            result[key] = value
    return result


class Settings:
    """Manages application settings with TOML persistence."""

    def __init__(self, config_path: Optional[Path] = None):
        self._config_path = config_path or CONFIG_FILE
        self._config: Dict[str, Any] = {}
        self._load()

    def _load(self):
        """Load settings from file, falling back to defaults."""
        # Load defaults first
        if DEFAULT_SETTINGS_PATH.exists():
            with open(DEFAULT_SETTINGS_PATH, 'r', encoding='utf-8') as f:
                self._config = toml.load(f)
        else:
            self._config = self._get_hardcoded_defaults()

        # Overlay user settings if they exist
        if self._config_path.exists():
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    user_config = toml.load(f)
                self._config = _deep_update(self._config, user_config)
            except Exception:
                pass  # Use defaults on error

    def _get_hardcoded_defaults(self) -> dict:
        """Fallback defaults if TOML file is missing."""
        return {
            "cosmology": {
                "H0": 67.4,
                "Omega_m": 0.315,
                "Omega_L": 0.685,
                "preset": "planck2018",
            },
            "rotation_curve": {
                "ml_disk": 0.5,
                "ml_bulge": 0.7,
                "halo_model": "ISO",
                "use_Hz": False,
            },
            "snia": {
                "max_display_points": 500,
                "downsample_method": "density",
                "use_log_downsample": True,
                "x_log_scale": True,
                "y_log_dl": False,
                "reference_color": "",
                "reference_linestyle": "-.",
            },
            "appearance": {
                "theme": "dark",
                "palette": "colorbrewer",
                "marker_size": 4,
                "line_width": 1.5,
            },
            "models": {},
        }

    def save(self):
        """Save current settings to file."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, 'w', encoding='utf-8') as f:
            toml.dump(self._config, f)

    def get(self, *keys, default=None) -> Any:
        """Get a nested setting value."""
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, *keys, value: Any, save: bool = True):
        """Set a nested setting value."""
        if len(keys) == 0:
            return

        # Navigate to parent
        current = self._config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set value
        current[keys[-1]] = value

        if save:
            self.save()

    # Convenience properties for common settings
    @property
    def H0(self) -> float:
        return self.get("cosmology", "H0", default=67.4)

    @H0.setter
    def H0(self, value: float):
        self.set("cosmology", "H0", value=value)

    @property
    def Omega_m(self) -> float:
        return self.get("cosmology", "Omega_m", default=0.315)

    @Omega_m.setter
    def Omega_m(self, value: float):
        self.set("cosmology", "Omega_m", value=value)

    @property
    def Omega_L(self) -> float:
        return self.get("cosmology", "Omega_L", default=0.685)

    @Omega_L.setter
    def Omega_L(self, value: float):
        self.set("cosmology", "Omega_L", value=value)

    @property
    def Omega_k(self) -> float:
        return 1.0 - self.Omega_m - self.Omega_L

    @property
    def theme(self) -> str:
        return self.get("appearance", "theme", default="dark")

    @theme.setter
    def theme(self, value: str):
        self.set("appearance", "theme", value=value)

    @property
    def palette(self) -> str:
        return self.get("appearance", "palette", default="colorbrewer")

    @palette.setter
    def palette(self, value: str):
        self.set("appearance", "palette", value=value)

    @property
    def halo_model(self) -> str:
        return self.get("rotation_curve", "halo_model", default="ISO")

    @halo_model.setter
    def halo_model(self, value: str):
        self.set("rotation_curve", "halo_model", value=value)

    @property
    def ml_disk(self) -> float:
        return self.get("rotation_curve", "ml_disk", default=0.5)

    @ml_disk.setter
    def ml_disk(self, value: float):
        self.set("rotation_curve", "ml_disk", value=value)

    @property
    def ml_bulge(self) -> float:
        return self.get("rotation_curve", "ml_bulge", default=0.7)

    @ml_bulge.setter
    def ml_bulge(self, value: float):
        self.set("rotation_curve", "ml_bulge", value=value)

    @property
    def max_display_points(self) -> int:
        return self.get("snia", "max_display_points", default=500)

    @max_display_points.setter
    def max_display_points(self, value: int):
        self.set("snia", "max_display_points", value=value)

    @property
    def cosmo_models(self) -> Dict[str, dict]:
        return self.get("models", default={})

    def get_enabled_models(self) -> Dict[str, dict]:
        """Get only enabled cosmology models."""
        return {
            name: model for name, model in self.cosmo_models.items()
            if model.get("enabled", False)
        }

    def apply_preset(self, preset_name: str):
        """Apply a cosmological parameter preset."""
        from .constants import COSMO_PRESETS
        if preset_name in COSMO_PRESETS:
            preset = COSMO_PRESETS[preset_name]
            self.H0 = preset["H0"]
            self.Omega_m = preset["Omega_m"]
            self.Omega_L = preset["Omega_L"]
            self.set("cosmology", "preset", value=preset_name)

    def to_dict(self) -> dict:
        """Return full config as dictionary."""
        return self._config.copy()


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings():
    """Reset settings to defaults."""
    global _settings
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
    _settings = Settings()
    return _settings
