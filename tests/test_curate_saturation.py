from pathlib import Path

from PIL import Image

from curate import estimate_image_saturation, is_image_valid_wallpaper


def make_image(path: Path, color: tuple[int, int, int]) -> None:
    img = Image.new("RGB", (2000, 1200), color=color)
    img.save(path)


def test_estimate_image_saturation_grayscale(tmp_path):
    gray = tmp_path / "gray.jpg"
    make_image(gray, (128, 128, 128))

    sat = estimate_image_saturation(gray)
    assert sat < 0.01


def test_min_saturation_blocks_bw(tmp_path):
    gray = tmp_path / "gray.jpg"
    make_image(gray, (50, 50, 50))

    assert is_image_valid_wallpaper(gray, min_saturation=0.05) is False


def test_min_saturation_allows_color(tmp_path):
    red = tmp_path / "red.jpg"
    make_image(red, (255, 0, 0))

    assert is_image_valid_wallpaper(red, min_saturation=0.05) is True


def test_default_allows_bw(tmp_path):
    gray = tmp_path / "gray.jpg"
    make_image(gray, (80, 80, 80))

    assert is_image_valid_wallpaper(gray, min_saturation=None) is True
