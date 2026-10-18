"""Configuration loading and hashing (§0.4, §32, BASE-1, INV-8).

All tunables come from padya/config/*.yaml. `config_sha256` hashes the canonical
JSON of everything that can change a result, so outputs are traceable.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import yaml

from padya.errors import ConfigError

CONFIG_DIR = Path(__file__).parent / "config"
_FILES = ("weights", "profiles", "metres", "frames", "authorities")


def freeze(value: Any) -> Any:
    """Recursively freeze JSON-like data (dict → read-only mapping, list → tuple)."""
    if isinstance(value, Mapping):
        return MappingProxyType({k: freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(v) for v in value)
    return value


def thaw(value: Any) -> Any:
    """Inverse of `freeze` for serialisation."""
    if isinstance(value, Mapping):
        return {k: thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [thaw(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(thaw(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(slots=True, frozen=True)
class Config:
    weights: Mapping[str, Any]
    profiles: Mapping[str, Any]
    metres: Mapping[str, Any]
    frames: Mapping[str, Any]
    authorities: Mapping[str, Any]
    profile_name: str
    baseline_mode: str
    tier: str

    @property
    def profile(self) -> Mapping[str, Any]:
        return self.profiles["profiles"][self.profile_name]

    @property
    def mode(self) -> Mapping[str, Any]:
        return self.profiles["baseline_modes"][self.baseline_mode]

    @property
    def registry_version(self) -> str:
        return str(self.metres["registry_version"])

    def sha256(self) -> str:
        payload = {
            "weights": self.weights, "profiles": self.profiles, "metres": self.metres,
            "frames": self.frames, "authorities": self.authorities,
            "profile_name": self.profile_name, "baseline_mode": self.baseline_mode,
            "tier": self.tier,
        }
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _read_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc


def load_config(
    *,
    profile: str = "classical_strict",
    baseline_mode: str = "BASE-A",
    tier: str = "T",
    config_dir: Path = CONFIG_DIR,
) -> Config:
    data = {name: freeze(_read_yaml(config_dir / f"{name}.yaml")) for name in _FILES}
    if profile not in data["profiles"]["profiles"]:
        raise ConfigError(f"unknown profile {profile!r}")
    if baseline_mode not in data["profiles"]["baseline_modes"]:
        raise ConfigError(f"unknown baseline mode {baseline_mode!r}; BASE-B is not built yet")
    if tier not in ("T", "P", "R", "unspecified"):
        raise ConfigError(f"unknown tier {tier!r}")
    return Config(
        weights=data["weights"], profiles=data["profiles"], metres=data["metres"],
        frames=data["frames"], authorities=data["authorities"],
        profile_name=profile, baseline_mode=baseline_mode, tier=tier,
    )
