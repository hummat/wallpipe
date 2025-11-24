#!/usr/bin/env python3
"""
Step 2: curate wallpapers from the downloaded pool into a flat directory.

Curated images go to:
    CURATED_DIR (see wallpaper_common for config)
"""

from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path
from typing import Iterable, List

from PIL import Image

from wallpaper_common import ensure_dir, get_artist_sources, is_image_file, resolve_paths

# Minimal resolution for wallpapers
MIN_WIDTH: int = 1920
MIN_HEIGHT: int = 1080

# Max curated images per artist (keeps things balanced)
MAX_PER_ARTIST: int = 40


def is_image_valid_wallpaper(path: Path) -> bool:
    """
    Check if the image is:
    - A valid image file we can open
    - At least MIN_WIDTH x MIN_HEIGHT in some orientation
    - Landscape (width >= height)
    """
    try:
        with Image.open(path) as img:
            width, height = img.size
    except Exception:
        return False

    # Landscape only
    if width < height:
        return False

    # Resolution check
    if width >= MIN_WIDTH and height >= MIN_HEIGHT:
        return True

    return False


def collect_valid_images(artist_download_dir: Path) -> List[Path]:
    """
    Find all images in `artist_download_dir` that pass the wallpaper filter.
    """
    candidates: List[Path] = []
    for path in artist_download_dir.rglob("*"):
        if not path.is_file():
            continue
        if not is_image_file(path):
            continue
        if is_image_valid_wallpaper(path):
            candidates.append(path)
    return candidates


def curate_artist(artist_slug: str, download_root: Path, curated_dir: Path) -> None:
    """
    For a given artist:
    - collect landscape, large-enough images from _downloaded/<artist_slug>
    - randomly pick up to MAX_PER_ARTIST
    - copy into the flat CURATED_DIR, with slug-prefixed filenames
    """
    artist_download_dir: Path = download_root / artist_slug

    if not artist_download_dir.exists():
        print(f"[curate] No download dir for {artist_slug}, skipping.")
        return

    images: List[Path] = collect_valid_images(artist_download_dir)
    if not images:
        print(f"[curate] No valid landscape images (>= {MIN_WIDTH}x{MIN_HEIGHT}) for {artist_slug}")
        return

    random.shuffle(images)
    selected: List[Path] = images[:MAX_PER_ARTIST]

    print(f"[curate] {artist_slug}: {len(images)} valid images, selecting {len(selected)}")

    for src in selected:
        # Prefix with artist slug to avoid filename collisions
        dest_name = f"{artist_slug}__{src.name}"
        dest = curated_dir / dest_name
        shutil.copy2(src, dest)


def curate_artists(
    artists: Iterable[str] | None = None,
    download_root: Path | None = None,
    curated_dir: Path | None = None,
    clear_curated: bool = True,
) -> None:
    """
    Curate wallpapers from the downloaded pool into CURATED_DIR.
    """
    paths = resolve_paths(download_root=download_root, curated_dir=curated_dir)
    download_root = paths["download_root"]
    curated_dir = paths["curated_dir"]

    ensure_dir(download_root)
    ensure_dir(curated_dir)

    artist_slugs: Iterable[str] = artists or get_artist_sources().keys()

    print("\n[curate] Filtering and balancing per artist...")

    if clear_curated:
        for existing in curated_dir.iterdir():
            if existing.is_file():
                existing.unlink()

    for slug in artist_slugs:
        curate_artist(slug, download_root=download_root, curated_dir=curated_dir)

    print("\n[curate] Done.")
    print(f"[curate] Output directory: {curated_dir}")
    print(
        "[curate] All curated images are landscape, filtered by resolution, and limited per artist."
    )


def parse_args() -> argparse.Namespace:  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="Step 2: curate wallpapers from the downloaded pool."
    )
    parser.add_argument(
        "download_dir",
        nargs="?",
        default=Path.cwd() / "_downloaded",
        type=Path,
        help="Source directory containing per-artist downloads (default: ./_downloaded).",
    )
    parser.add_argument(
        "curated_dir",
        nargs="?",
        default=Path.cwd() / "_curated",
        type=Path,
        help="Destination flat directory for curated wallpapers (default: ./_curated).",
    )
    parser.add_argument(
        "--no-clear-curated",
        action="store_true",
        help="Do not wipe CURATED_DIR before curating.",
    )
    return parser.parse_args()


def main() -> None:  # pragma: no cover
    args = parse_args()
    artists = get_artist_sources()
    clear_flag = not args.no_clear_curated
    curate_artists(
        artists=artists.keys(),
        download_root=args.download_dir,
        curated_dir=args.curated_dir,
        clear_curated=clear_flag,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
