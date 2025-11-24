import random
from pathlib import Path

from PIL import Image, ImageDraw

import curate


def make_image(path: Path, size: tuple[int, int]) -> None:
    img = Image.new("RGB", size, color=(10, 20, 30))
    img.save(path)


def test_is_image_valid_wallpaper_sizes(tmp_path):
    big_landscape = tmp_path / "big.jpg"
    big_portrait = tmp_path / "bigp.jpg"
    small = tmp_path / "small.jpg"
    webp_landscape = tmp_path / "good.webp"

    make_image(big_landscape, (2000, 1200))
    make_image(big_portrait, (1200, 2000))
    make_image(small, (800, 600))
    make_image(webp_landscape, (1920, 1080))

    assert curate.is_image_valid_wallpaper(big_landscape) is True
    assert curate.is_image_valid_wallpaper(big_portrait) is False
    assert curate.is_image_valid_wallpaper(small) is False
    assert curate.is_image_valid_wallpaper(webp_landscape) is True


def test_collect_valid_images_and_curate_artist(tmp_path, monkeypatch):
    download_root = tmp_path / "_downloaded"
    curated_dir = tmp_path / "_curated"
    artist = "foo"
    artist_dir = download_root / artist
    artist_dir.mkdir(parents=True)

    good = artist_dir / "good.jpg"
    bad = artist_dir / "bad.jpg"
    nested = artist_dir / "nested"
    nested.mkdir()
    nested_good = nested / "good2.png"
    make_image(good, (1920, 1080))
    make_image(bad, (800, 800))
    make_image(nested_good, (3000, 2000))

    curated_dir.mkdir(parents=True)

    # deterministic order
    monkeypatch.setattr(random, "shuffle", lambda lst: lst)

    curate.curate_artist(
        artist, download_root, curated_dir, min_saturation=None, dedup_hamming=None
    )

    curated_files = sorted(p.name for p in curated_dir.iterdir())
    assert curated_files == [f"{artist}__good.jpg", f"{artist}__good2.png"]


def test_curate_artists_clears_dest(tmp_path, monkeypatch):
    download_root = tmp_path / "_downloaded"
    curated_dir = tmp_path / "_curated"
    artist = "foo"
    artist_dir = download_root / artist
    artist_dir.mkdir(parents=True)
    make_image(artist_dir / "good.jpg", (1920, 1080))

    # existing file to be cleared
    curated_dir.mkdir(parents=True)
    old = curated_dir / "old.jpg"
    make_image(old, (1920, 1080))

    monkeypatch.setattr(random, "shuffle", lambda lst: lst)

    curate.curate_artists(
        artists=[artist],
        download_root=download_root,
        curated_dir=curated_dir,
        clear_curated=True,
        min_saturation=None,
        dedup_hamming=None,
    )

    files = [p.name for p in curated_dir.iterdir()]
    assert files == [f"{artist}__good.jpg"]


def test_curate_artists_no_clear_keeps_existing(tmp_path, monkeypatch):
    download_root = tmp_path / "_downloaded"
    curated_dir = tmp_path / "_curated"
    artist = "foo"
    artist_dir = download_root / artist
    artist_dir.mkdir(parents=True)
    make_image(artist_dir / "good.jpg", (1920, 1080))

    curated_dir.mkdir(parents=True)
    keep = curated_dir / "keep.jpg"
    make_image(keep, (1920, 1080))

    monkeypatch.setattr(random, "shuffle", lambda lst: lst)

    curate.curate_artists(
        artists=[artist],
        download_root=download_root,
        curated_dir=curated_dir,
        clear_curated=False,
        min_saturation=None,
        dedup_hamming=None,
    )

    names = sorted(p.name for p in curated_dir.iterdir())
    assert names == ["foo__good.jpg", "keep.jpg"]


def test_curate_artist_missing_dir(tmp_path, capsys):
    download_root = tmp_path / "_downloaded"
    curated_dir = tmp_path / "_curated"
    curated_dir.mkdir(parents=True)

    curate.curate_artist(
        "missing",
        download_root,
        curated_dir,
        min_saturation=None,
        dedup_hamming=None,
    )

    out = capsys.readouterr().out
    assert "No download dir for missing" in out


def test_dedup_hamming_skips_near_duplicates(tmp_path, monkeypatch):
    download_root = tmp_path / "_downloaded"
    curated_dir = tmp_path / "_curated"
    artist = "foo"
    artist_dir = download_root / artist
    artist_dir.mkdir(parents=True)

    def make_colored(path: Path, color: int) -> None:
        img = Image.new("RGB", (1920, 1080), color=(color, color, color))
        img.save(path)

    orig = artist_dir / "a.jpg"
    dup = artist_dir / "b.jpg"
    different = artist_dir / "c.jpg"
    make_colored(orig, 100)
    make_colored(dup, 102)  # tiny change, likely within hamming threshold
    # make a very different hash (half black, half white)
    img = Image.new("RGB", (1920, 1080), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle((960, 0, 1919, 1079), fill=(255, 255, 255))
    img.save(different)

    curated_dir.mkdir(parents=True)
    monkeypatch.setattr(random, "shuffle", lambda lst: lst)

    curate.curate_artist(
        artist,
        download_root,
        curated_dir,
        min_saturation=None,
        dedup_hamming=5,
    )

    names = sorted(p.name for p in curated_dir.iterdir())
    # Should keep one of the near-duplicates plus the different one
    assert len(names) == 2
    assert any(name.startswith("foo__a") or name.startswith("foo__b") for name in names)
    assert any(name.startswith("foo__c") for name in names)
