#!/usr/bin/env python3
"""
Step 1: download/update raw images per artist using gallery-dl.

Downloads go to:
    DOWNLOAD_ROOT/<artist_slug>/ (see common.py for config)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, List, Mapping

from common import ensure_dir, get_artist_sources, resolve_paths

DEFAULT_ABORT_AFTER = 20


def run_gallery_dl(target_dir: Path, url: str, abort_after: int = DEFAULT_ABORT_AFTER) -> None:
    """
    Run gallery-dl to download from `url` into `target_dir`.

    abort_after: stop after N consecutive skipped files (0 disables early abort).
    """
    ensure_dir(target_dir)
    binary = shutil.which("gallery-dl")
    if binary is None:
        raise FileNotFoundError("gallery-dl not found on PATH")

    cmd: List[str] = [binary, "-d", str(target_dir)]
    if abort_after > 0:
        cmd.extend(["--abort", str(abort_after)])
    cmd.append(url)

    print(f"\n[gallery-dl] {url}")
    print(f"  → {target_dir}")
    subprocess.run(cmd, check=True)


def download_artists(
    artists: Mapping[str, Iterable[str]],
    download_root: Path,
    abort_after: int = DEFAULT_ABORT_AFTER,
) -> None:
    """
    Download/update all raw images for the given artists.
    """
    ensure_dir(download_root)

    for slug, urls in artists.items():
        artist_download_dir: Path = download_root / slug
        for url in urls:
            try:
                run_gallery_dl(artist_download_dir, url, abort_after=abort_after)
            except FileNotFoundError:
                print(
                    "ERROR: `gallery-dl` not found. Install it, e.g.:\n"
                    "  sudo pacman -S gallery-dl\n"
                    "or\n"
                    "  pip install --user gallery-dl"
                )
                return
            except subprocess.CalledProcessError as exc:
                print(f"ERROR: gallery-dl failed for {slug} ({url}) with code {exc.returncode}")


def parse_args() -> argparse.Namespace:  # pragma: no cover
    def non_negative_int(value: str) -> int:
        parsed = int(value)
        if parsed < 0:
            raise argparse.ArgumentTypeError("abort-after must be >= 0")
        return parsed

    parser = argparse.ArgumentParser(
        description="Step 1: download/update raw images per artist using gallery-dl."
    )
    parser.add_argument(
        "--abort-after",
        type=non_negative_int,
        default=DEFAULT_ABORT_AFTER,
        metavar="N",
        help=(
            "Stop gallery-dl after N consecutive skipped files (existing/archived). "
            "Use 0 to disable early abort."
        ),
    )
    parser.add_argument(
        "download_dir",
        nargs="?",
        default=Path.cwd() / "_downloaded",
        type=Path,
        help="Directory for per-artist downloads (default: ./_downloaded).",
    )
    return parser.parse_args()


def main() -> None:  # pragma: no cover
    args = parse_args()
    artists = get_artist_sources()
    paths = resolve_paths(download_root=args.download_dir)
    download_artists(artists, download_root=paths["download_root"], abort_after=args.abort_after)


if __name__ == "__main__":  # pragma: no cover
    main()
