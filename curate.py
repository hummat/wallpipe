#!/usr/bin/env python3
"""
Step 2: curate wallpapers from the downloaded pool into a flat directory.

Curated images go to:
    CURATED_DIR (see common.py for config)
"""

from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path
from typing import Iterable, List, Optional, cast

from PIL import Image

from common import ensure_dir, get_artist_sources, is_image_file, resolve_paths

# Minimal resolution for wallpapers
MIN_WIDTH: int = 1920
MIN_HEIGHT: int = 1080

# Max curated images per artist (keeps things balanced)
MAX_PER_ARTIST: int = 25
DEFAULT_MIN_SATURATION: float = 0.0  # disabled unless overridden
DEFAULT_DEDUP_HAMMING: int | None = None


def estimate_image_saturation(path: Path, sample_size: int = 512) -> float:
    """
    Estimate median saturation (0-1) using a downscaled HSV image.
    """
    with Image.open(path).convert("RGB") as img:
        img = img.copy()
        img.thumbnail((sample_size, sample_size))
        hsv = img.convert("HSV")
        _, s_channel, _ = hsv.split()
        sats = list(cast(Iterable[int], s_channel.getdata()))

    if not sats:
        return 0.0

    sats.sort()
    mid = len(sats) // 2
    if len(sats) % 2 == 0:
        median_val = (sats[mid - 1] + sats[mid]) / 2
    else:
        median_val = sats[mid]

    return float(median_val) / 255.0


def average_hash(path: Path, hash_size: int = 8) -> int:
    """
    Simple average hash (aHash) for perceptual deduplication.
    Returns an int bitmask of length hash_size * hash_size.
    """
    with Image.open(path).convert("L") as img:
        img = img.copy()
        img = img.resize((hash_size, hash_size))
        pixels = list(cast(Iterable[int], img.getdata()))

    if not pixels:
        return 0

    avg = sum(pixels) / len(pixels)
    bits = 0
    for px in pixels:
        bits = (bits << 1) | (1 if px >= avg else 0)
    return bits


def hamming_distance(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def is_image_valid_wallpaper(path: Path, min_saturation: Optional[float] = None) -> bool:
    """
    Check if the image is:
    - A valid image file we can open
    - At least MIN_WIDTH x MIN_HEIGHT in some orientation
    - Landscape (width >= height)
    - Optionally meets a minimum saturation threshold
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
        pass
    else:
        return False

    if min_saturation is not None and min_saturation > 0:
        try:
            sat = estimate_image_saturation(path)
        except Exception:
            return False
        if sat < min_saturation:
            return False

    return True


def collect_valid_images(artist_download_dir: Path, min_saturation: Optional[float]) -> List[Path]:
    """
    Find all images in `artist_download_dir` that pass the wallpaper filter.
    """
    candidates: List[Path] = []
    for path in artist_download_dir.rglob("*"):
        if not path.is_file():
            continue
        if not is_image_file(path):
            continue
        if is_image_valid_wallpaper(path, min_saturation=min_saturation):
            candidates.append(path)
    return candidates


def curate_artist(
    artist_slug: str,
    download_root: Path,
    curated_dir: Path,
    min_saturation: Optional[float],
    dedup_hamming: Optional[int],
) -> None:
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

    images: List[Path] = collect_valid_images(artist_download_dir, min_saturation=min_saturation)
    if dedup_hamming is not None:
        kept: List[Path] = []
        hashes: List[int] = []
        for path in images:
            try:
                h = average_hash(path)
            except Exception as exc:
                print(f"[curate] hash failed for {path}: {exc}")
                continue
            if any(hamming_distance(h, existing) <= dedup_hamming for existing in hashes):
                print(f"[curate] dedup skip ({dedup_hamming}) {path.name}")
                continue
            hashes.append(h)
            kept.append(path)
        images = kept
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
    min_saturation: Optional[float] = None,
    dedup_hamming: Optional[int] = None,
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
        curate_artist(
            slug,
            download_root=download_root,
            curated_dir=curated_dir,
            min_saturation=min_saturation,
            dedup_hamming=dedup_hamming,
        )

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
        default=Path.cwd() / "downloaded",
        type=Path,
        help="Source directory containing per-artist downloads (default: ./downloaded).",
    )
    parser.add_argument(
        "curated_dir",
        nargs="?",
        default=Path.cwd() / "curated",
        type=Path,
        help="Destination flat directory for curated wallpapers (default: ./curated).",
    )
    parser.add_argument(
        "--no-clear-curated",
        action="store_true",
        help="Do not wipe CURATED_DIR before curating.",
    )
    parser.add_argument(
        "--min-saturation",
        type=float,
        default=None,
        help=(
            "Minimum median saturation (0-1) to keep an image. "
            "Use to skip black-and-white/very low-color images. Disabled by default."
        ),
    )
    parser.add_argument(
        "--skip-bw",
        action="store_true",
        help="Shorthand for --min-saturation 0.08 to drop low-saturation images.",
    )
    parser.add_argument(
        "--dedup-hamming",
        type=int,
        default=None,
        help=(
            "Per-artist perceptual dedup using aHash/Hamming distance. "
            "Skip images within this distance of a prior one (e.g., 5-10). "
            "Disabled by default."
        ),
    )
    return parser.parse_args()


def main() -> None:  # pragma: no cover
    args = parse_args()
    artists = get_artist_sources()
    clear_flag = not args.no_clear_curated
    min_saturation: Optional[float] = args.min_saturation
    if min_saturation is None and args.skip_bw:
        min_saturation = 0.08
    dedup_hamming: Optional[int] = args.dedup_hamming

    curate_artists(
        artists=artists.keys(),
        download_root=args.download_dir,
        curated_dir=args.curated_dir,
        clear_curated=clear_flag,
        min_saturation=min_saturation,
        dedup_hamming=dedup_hamming,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
