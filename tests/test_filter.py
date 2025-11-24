from pathlib import Path
from typing import Dict, List

import torch
from PIL import Image

import filter as filt


def make_image(path: Path, size=(1920, 1080)) -> None:
    img = Image.new("RGB", size, color=(123, 123, 123))
    img.save(path)


def test_filter_wallpapers_respects_score_and_clears_dest(tmp_path, monkeypatch):
    source = tmp_path / "_curated"
    dest = tmp_path / "_curated_aesthetic"
    source.mkdir()
    dest.mkdir()
    # preexisting file to be cleared
    pre = dest / "old.jpg"
    make_image(pre)

    good = source / "good.jpg"
    bad = source / "bad.jpg"
    make_image(good)
    make_image(bad)

    scores: Dict[str, float] = {"good.jpg": 6.0, "bad.jpg": 4.0}

    monkeypatch.setattr(filt, "get_aesthetic_score", lambda p: scores[p.name])
    monkeypatch.setattr(filt, "image_matches_block_keywords", lambda *args, **kwargs: False)

    copied: List[tuple[Path, Path]] = []
    monkeypatch.setattr(
        filt.shutil,
        "copy2",
        lambda src, dst: copied.append((Path(src), Path(dst))),
    )

    filt.filter_wallpapers(
        source_dir=source,
        dest_dir=dest,
        min_score=5.0,
        block_keywords=[],
        dry_run=False,
    )

    assert (dest / "bad.jpg").exists() is False
    # copy was attempted for the good image
    assert copied == [(good, dest / "good.jpg")]
    # old file cleared
    assert not pre.exists()


def test_filter_wallpapers_respects_block_keywords(tmp_path, monkeypatch):
    source = tmp_path / "_curated"
    dest = tmp_path / "_curated_aesthetic"
    source.mkdir()
    dest.mkdir()

    img = source / "car.jpg"
    make_image(img)

    monkeypatch.setattr(filt, "get_aesthetic_score", lambda p: 10.0)
    monkeypatch.setattr(filt, "image_matches_block_keywords", lambda *args, **kwargs: True)

    copied: list[tuple[Path, Path]] = []
    monkeypatch.setattr(
        filt.shutil,
        "copy2",
        lambda src, dst: copied.append((Path(src), Path(dst))),
    )

    filt.filter_wallpapers(
        source_dir=source,
        dest_dir=dest,
        min_score=5.0,
        block_keywords=["car"],
        dry_run=False,
    )

    assert copied == []


def test_filter_wallpapers_dry_run_skips_copy(tmp_path, monkeypatch):
    source = tmp_path / "_curated"
    dest = tmp_path / "_curated_aesthetic"
    source.mkdir()
    dest.mkdir()

    img = source / "good.jpg"
    make_image(img)

    monkeypatch.setattr(filt, "get_aesthetic_score", lambda p: 10.0)
    monkeypatch.setattr(filt, "image_matches_block_keywords", lambda *args, **kwargs: False)

    copied: list[tuple[Path, Path]] = []
    monkeypatch.setattr(
        filt.shutil,
        "copy2",
        lambda src, dst: copied.append((Path(src), Path(dst))),
    )

    filt.filter_wallpapers(
        source_dir=source,
        dest_dir=dest,
        min_score=5.0,
        block_keywords=[],
        dry_run=True,
    )

    assert copied == []
    # dry-run should not clear dest
    assert dest.exists()


def test_load_models_and_scoring_stubbed(tmp_path, monkeypatch):
    class DummyPredictor:
        def __init__(self):
            self.to_called = False
            self.eval_called = False

        def to(self, device):
            self.to_called = True
            return self

        def eval(self):
            self.eval_called = True

        def __call__(self, **kwargs):
            return type("Out", (), {"logits": torch.tensor([7.5])})

    class DummyProcessor:
        def __call__(self, **kwargs):
            return {"x": torch.tensor([1])}

    class DummyClipModel:
        def __init__(self):
            self.to_called = False
            self.eval_called = False

        def to(self, device):
            self.to_called = True
            return self

        def eval(self):
            self.eval_called = True

        def __call__(self, **kwargs):
            logits = torch.tensor([[0.2, 0.8]])
            return type("Out", (), {"logits_per_image": logits})

    monkeypatch.setattr(
        filt.AestheticsPredictorV1,
        "from_pretrained",
        lambda _id: DummyPredictor(),
    )
    monkeypatch.setattr(
        filt.CLIPProcessor,
        "from_pretrained",
        lambda _id: DummyProcessor(),
    )
    monkeypatch.setattr(
        filt.CLIPModel,
        "from_pretrained",
        lambda _id: DummyClipModel(),
    )

    img_path = tmp_path / "img.jpg"
    make_image(img_path)

    score = filt.get_aesthetic_score(img_path)
    assert score == 7.5

    blocked = filt.image_matches_block_keywords(img_path, ["car", "tree"], 0.5)
    assert blocked is True
