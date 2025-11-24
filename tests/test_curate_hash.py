from pathlib import Path

from PIL import Image

from curate import average_hash, hamming_distance


def make_img(path: Path, color: tuple[int, int, int]) -> None:
    img = Image.new("RGB", (64, 64), color=color)
    img.save(path)


def test_average_hash_identical(tmp_path):
    a = tmp_path / "a.jpg"
    b = tmp_path / "b.jpg"
    make_img(a, (100, 100, 100))
    make_img(b, (100, 100, 100))

    ha = average_hash(a)
    hb = average_hash(b)

    assert hamming_distance(ha, hb) == 0


def test_average_hash_very_different(tmp_path):
    a = tmp_path / "pattern1.jpg"
    b = tmp_path / "pattern2.jpg"
    img1 = Image.new("RGB", (64, 64), color=(0, 0, 0))
    for x in range(32, 64):
        for y in range(32, 64):
            img1.putpixel((x, y), (255, 255, 255))
    img1.save(a)

    img2 = Image.new("RGB", (64, 64), color=(255, 255, 255))
    for x in range(32, 64):
        for y in range(32, 64):
            img2.putpixel((x, y), (0, 0, 0))
    img2.save(b)

    ha = average_hash(a)
    hb = average_hash(b)

    assert hamming_distance(ha, hb) > 20
