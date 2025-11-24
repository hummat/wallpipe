#!/usr/bin/env python3
"""
Shared paths and helpers for the wallpaper pipeline.

This is used by:
    - download.py  (step 1: download raw images)
    - curate.py    (step 2: curate wallpapers)
    - filter.py    (step 3: aesthetic filtering)
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Default paths (can be overridden by config)
DEFAULT_WALLPAPER_ROOT: Path = Path.home() / "Pictures" / "wallpaper"
DEFAULT_DOWNLOAD_ROOT: Path = DEFAULT_WALLPAPER_ROOT / "downloaded"
DEFAULT_CURATED_DIR: Path = DEFAULT_WALLPAPER_ROOT / "curated"

# Config lookup locations (first one that exists wins)
CONFIG_PATHS: Tuple[Path, ...] = (
    # Explicit override via env var
    Path(Path.cwd() / "wallpipe.toml"),
    Path.home() / ".config" / "wallpipe" / "config.toml",
)

# Lazily populated cache
_loaded_config: Dict | None = None
_resolved_paths: Dict[str, Path] | None = None


def _load_config() -> Dict:
    """
    Load config from the first existing file among CONFIG_PATHS or
    the path set in $WALLPIPE_CONFIG. Missing file is fine; returns {}.
    """
    global _loaded_config
    if _loaded_config is not None:
        return _loaded_config

    env_override = os.environ.get("WALLPIPE_CONFIG", "")
    env_path = Path(env_override).expanduser() if env_override else None

    search_order = ((env_path,) if env_path else ()) + CONFIG_PATHS

    for candidate in search_order:
        if candidate.is_file():
            try:
                with candidate.open("rb") as fh:
                    _loaded_config = tomllib.load(fh)  # type: ignore[name-defined]
                break
            except Exception:
                _loaded_config = {}
                break
    else:
        _loaded_config = {}

    return _loaded_config


def resolve_paths(
    wallpaper_root: Optional[Path | str] = None,
    download_root: Optional[Path | str] = None,
    curated_dir: Optional[Path | str] = None,
) -> Dict[str, Path]:
    """
    Resolve wallpaper paths using provided overrides, then config, then defaults.
    """
    cfg = _load_config()
    paths_cfg = cfg.get("paths", {}) if isinstance(cfg, dict) else {}

    wall_root = Path(
        wallpaper_root or paths_cfg.get("wallpaper_root", DEFAULT_WALLPAPER_ROOT)
    ).expanduser()
    dl_root = Path(
        download_root or paths_cfg.get("download_root", wall_root / "downloaded")
    ).expanduser()
    curated = Path(curated_dir or paths_cfg.get("curated_dir", wall_root / "curated")).expanduser()

    return {
        "wallpaper_root": wall_root,
        "download_root": dl_root,
        "curated_dir": curated,
    }


def _resolve_paths() -> Dict[str, Path]:
    """
    Backward-compatible cached resolver with no overrides (used for defaults).
    """
    global _resolved_paths
    if _resolved_paths is None:
        _resolved_paths = resolve_paths()
    return _resolved_paths


# Resolved paths (public, keeps existing names)
WALLPAPER_ROOT: Path = _resolve_paths()["wallpaper_root"]
DOWNLOAD_ROOT: Path = _resolve_paths()["download_root"]
CURATED_DIR: Path = _resolve_paths()["curated_dir"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def is_image_file(path: Path) -> bool:
    """
    Basic extension check. PIL will be the real gatekeeper.
    """
    ext = path.suffix.lower()
    return ext in {".jpg", ".jpeg", ".png", ".webp"}


DEFAULT_ARTIST_SOURCES: Dict[str, List[str]] = {
    # Maciej Kuciara
    "maciej_kuciara": [
        "https://www.artstation.com/maciej",
        "https://www.behance.net/maciejkuciara",
    ],
    # Jama Jurabaev
    "jama_jurabaev": [
        "https://www.artstation.com/jama",
        "https://jamajurabaev.deviantart.com/",
    ],
    # Ian McQue
    "ian_mcque": [
        "https://www.artstation.com/mcque65",
        "https://mcque.deviantart.com/",
    ],
    # Paul Chadeisson
    "paul_chadeisson": [
        "https://www.artstation.com/pao",
        "https://www.behance.net/paulchadei99e8",
        "https://paooo.deviantart.com/",
    ],
    # Sparth (Nicolas Bouvier)
    "sparth": [
        "https://www.artstation.com/sparth",
    ],
    # Jan Urschel
    "jan_urschel": [
        "https://www.artstation.com/janurschel",
        "https://www.behance.net/janurschel",
        "https://janurschel.deviantart.com/",
    ],
    # Rob Tuytel
    "rob_tuytel": [
        "https://www.artstation.com/tuytel",
    ],
    # Ian Hubert
    "ian_hubert": [
        "https://www.artstation.com/ianhubert",
        "https://www.deviantart.com/mrdodobird",
    ],
}


def get_artist_sources() -> Dict[str, List[str]]:
    """
    Return mapping artist_slug -> list of URLs for gallery-dl.
    First takes artists from config, otherwise falls back to defaults.
    """
    cfg = _load_config()
    artists_cfg = cfg.get("artists") if isinstance(cfg, dict) else None
    if isinstance(artists_cfg, dict) and artists_cfg:
        return {k: list(v) for k, v in artists_cfg.items()}
    return DEFAULT_ARTIST_SOURCES.copy()
