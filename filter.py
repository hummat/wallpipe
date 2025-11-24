#!/usr/bin/env python3
"""
Step 3: filter curated wallpapers using an ML-based aesthetic score.

Intended to be run *after*:
    1) download.py
    2) curate.py

It uses the "simple-aesthetics-predictor" package, which wraps a
pre-trained CLIP-based aesthetics model from the Hugging Face Hub.

Setup (in the same Python environment your script uses):

    pip install torch transformers simple-aesthetics-predictor
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Any, List, cast

import torch
from aesthetics_predictor import AestheticsPredictorV1
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from common import is_image_file

# Aesthetic scoring model (CLIP + MLP head)
MODEL_ID: str = "shunk031/aesthetics-predictor-v1-vit-large-patch14"

# CLIP model for keyword-based filtering
CLIP_MODEL_ID: str = "openai/clip-vit-large-patch14"

DEFAULT_MIN_SCORE: float = 6.0

# Default keywords to avoid. Split into buckets so thresholds/prompts can differ.
DEFAULT_BLOCK_KEYWORDS_GENERAL: List[str] = [
    "car",
    "tank",
    "weapon",
    "gun",
    "rifle",
    "pistol",
    "mech",
    "robot",
    "soldier",
    "war",
    "zombie",
    "monster",
    "bike",
    "motorcycle",
    "motorbike",
    "wireframe",
    "game asset",
    "albedo",
    "diffuse",
    "normal map",
    "roughness",
    "metallic",
    "ao map",
    "specular",
    "height map",
]
DEFAULT_BLOCK_KEYWORDS_NSFW: List[str] = [
    "nude",
    "naked",
    "nsfw",
    "porn",
    "explicit",
    "gore",
    "violence",
    "sex",
    "sexual",
    "erotic",
    "hardcore",
    "hentai",
    "breast",
    "boobs",
    "nipple",
    "genitals",
    "penis",
    "vagina",
    "cum",
    "semen",
    "orgasm",
    "ejaculation",
    "masturbation",
    "fetish",
    "xxx",
    "escort",
    "onlyfans",
    "strip",
    "camgirl",
]

DEFAULT_BLOCK_THRESHOLD_GENERAL: float = 0.80
DEFAULT_BLOCK_THRESHOLD_NSFW: float = 0.70

# If True, destination dir is wiped before adding new images
CLEAR_DEST: bool = True

_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_aesthetic_predictor: AestheticsPredictorV1 | None = None
_aesthetic_processor: CLIPProcessor | None = None

_clip_model: CLIPModel | None = None
_clip_processor: CLIPProcessor | None = None


def load_aesthetic_model() -> tuple[AestheticsPredictorV1, CLIPProcessor]:
    """
    Lazily load the aesthetics predictor and its processor.
    """
    global _aesthetic_predictor, _aesthetic_processor

    if _aesthetic_predictor is None or _aesthetic_processor is None:
        print(f"[model] Loading aesthetics predictor: {MODEL_ID}")
        predictor = AestheticsPredictorV1.from_pretrained(MODEL_ID)
        processor = CLIPProcessor.from_pretrained(MODEL_ID)

        predictor = cast(AestheticsPredictorV1, predictor.to(_device))  # type: ignore[misc]
        predictor.eval()

        _aesthetic_predictor = predictor
        _aesthetic_processor = processor

    assert _aesthetic_predictor is not None
    assert _aesthetic_processor is not None
    predictor = cast(AestheticsPredictorV1, _aesthetic_predictor)
    processor = cast(CLIPProcessor, _aesthetic_processor)
    return predictor, processor


def load_clip_model() -> tuple[CLIPModel, CLIPProcessor]:
    """
    Lazily load CLIP model + processor for keyword filtering.
    """
    global _clip_model, _clip_processor

    if _clip_model is None or _clip_processor is None:
        print(f"[model] Loading CLIP model for keyword filtering: {CLIP_MODEL_ID}")
        clip_model = CLIPModel.from_pretrained(CLIP_MODEL_ID)
        clip_processor = CLIPProcessor.from_pretrained(CLIP_MODEL_ID)

        clip_model = cast(CLIPModel, clip_model.to(_device))  # type: ignore[misc]
        clip_model.eval()

        _clip_model = clip_model
        _clip_processor = clip_processor

    assert _clip_model is not None
    assert _clip_processor is not None
    clip_model = cast(CLIPModel, _clip_model)
    clip_processor = cast(CLIPProcessor, _clip_processor)
    return clip_model, clip_processor


def get_aesthetic_score(path: Path) -> float:
    """
    Compute an aesthetics score for the given image.
    """
    predictor, processor = load_aesthetic_model()

    with Image.open(path).convert("RGB") as img:
        inputs = processor(images=img, return_tensors="pt")  # type: ignore[call-arg]

    inputs = {k: v.to(_device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = predictor(**inputs)  # type: ignore[misc]

    score_tensor = outputs.logits
    return float(score_tensor.squeeze().item())


def build_clip_prompts(keywords: List[str], context: str = "general") -> List[str]:
    """
    Build text prompts for CLIP given keywords and a context.
    Context can be "general" (vehicles/war/etc.) or "nsfw" for explicit content.
    """
    if not keywords:
        return []

    if context == "nsfw":
        templates = [
            "an explicit photo of {}",
            "a pornographic image of {}",
            "an nsfw depiction of {}",
            "a nude photo of {}",
            "a naked person with {}",
        ]
    else:
        templates = [
            "a photo of {}",
            "an illustration of {}",
            "a realistic render of {}",
        ]

    prompts: List[str] = []
    for kw in keywords:
        prompts.extend(template.format(kw) for template in templates)
    return prompts


def image_matches_block_keywords(
    path: Path,
    keywords: List[str],
    threshold: float,
    context: str = "general",
) -> bool:
    """
    Use CLIP to estimate whether an image matches any of the blocked keywords.

    We compute CLIP similarity between the image and a set of prompts derived
    from the keywords, then treat high-probability matches as "blocked".
    """
    prompts = build_clip_prompts(keywords, context=context)
    if not prompts:
        return False

    model, processor = load_clip_model()

    processor_typed = cast(Any, processor)

    with Image.open(path).convert("RGB") as img:
        inputs = processor_typed(
            text=prompts,
            images=img,
            return_tensors="pt",
            padding=True,
        )

    inputs = {k: v.to(_device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)  # type: ignore[misc]

    logits_per_image = outputs.logits_per_image  # shape: [1, num_prompts]
    probs = logits_per_image.softmax(dim=1)
    max_prob = float(probs.max().item())

    return max_prob >= threshold


def collect_images(source_dir: Path) -> List[Path]:
    """
    Collect image files from the (flat) source directory.
    """
    images: List[Path] = []
    for path in source_dir.iterdir():
        if path.is_file() and is_image_file(path):
            images.append(path)
    return images


def filter_wallpapers(
    source_dir: Path,
    dest_dir: Path,
    min_score: float,
    block_keywords: List[str] | None = None,
    block_threshold: float = DEFAULT_BLOCK_THRESHOLD_GENERAL,
    block_keywords_nsfw: List[str] | None = None,
    block_threshold_nsfw: float = DEFAULT_BLOCK_THRESHOLD_NSFW,
    dry_run: bool = False,
) -> None:
    """
    Score all images in source_dir and copy those that meet the
    aesthetics threshold into dest_dir.
    """
    if not source_dir.exists():
        print(f"[error] Source directory does not exist: {source_dir}")
        return

    images = collect_images(source_dir)
    if not images:
        print(f"[info] No images found in {source_dir}")
        return

    dest_dir.mkdir(parents=True, exist_ok=True)

    if CLEAR_DEST and not dry_run:
        print(f"[info] Clearing destination directory: {dest_dir}")
        for existing in dest_dir.iterdir():
            if existing.is_file():
                existing.unlink()

    print(
        f"[info] Evaluating {len(images)} images from {source_dir} "
        f"with min aesthetics score {min_score:.2f}"
    )
    if block_keywords:
        print(
            f"[info] Blocking images that look like (general): "
            f"{', '.join(block_keywords)} "
            f"(threshold {block_threshold:.2f})"
        )
    if block_keywords_nsfw:
        print(
            f"[info] Blocking images that look like (nsfw): "
            f"{', '.join(block_keywords_nsfw)} "
            f"(threshold {block_threshold_nsfw:.2f})"
        )

    kept = 0
    for path in images:
        # First, apply keyword-based blocking if requested
        if block_keywords:
            try:
                if image_matches_block_keywords(
                    path, block_keywords, block_threshold, context="general"
                ):
                    print(f"[block] general keyword match  {path.name}")
                    continue
            except Exception as exc:  # pragma: no cover - defensive
                print(f"[warn] Keyword check failed for {path.name}: {exc}")
        if block_keywords_nsfw:
            try:
                if image_matches_block_keywords(
                    path, block_keywords_nsfw, block_threshold_nsfw, context="nsfw"
                ):
                    print(f"[block] nsfw keyword match  {path.name}")
                    continue
            except Exception as exc:  # pragma: no cover - defensive
                print(f"[warn] NSFW keyword check failed for {path.name}: {exc}")

        # Then apply aesthetics score threshold
        try:
            score = get_aesthetic_score(path)
        except Exception as exc:  # pragma: no cover - defensive
            print(f"[warn] Failed to score {path.name}: {exc}")
            continue

        print(f"[score] {score:5.2f}  {path.name}")

        if score < min_score:
            continue

        kept += 1
        if dry_run:
            continue

        dest_path = dest_dir / path.name
        shutil.copy2(path, dest_path)

    print(f"[summary] Kept {kept} / {len(images)} images (min score {min_score:.2f})")
    if not dry_run:
        print(f"[summary] Output directory: {dest_dir}")


def parse_args() -> argparse.Namespace:  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="Filter curated wallpapers using an ML-based aesthetic score."
    )
    parser.add_argument(
        "source",
        nargs="?",
        default=Path.cwd() / "curated",
        type=Path,
        help="Source directory of curated wallpapers (default: ./curated).",
    )
    parser.add_argument(
        "dest",
        nargs="?",
        default=Path.cwd() / "filtered",
        type=Path,
        help="Destination directory for high-scoring wallpapers (default: ./filtered).",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=DEFAULT_MIN_SCORE,
        help=f"Minimum aesthetics score to keep an image (default: {DEFAULT_MIN_SCORE})",
    )
    parser.add_argument(
        "--block-keyword",
        action="append",
        help=(
            "Keyword to avoid (e.g. 'car', 'weapon'). "
            "Can be specified multiple times. "
            "If omitted, a default vehicle/weapon blocklist is used."
        ),
    )
    parser.add_argument(
        "--block-keyword-general",
        action="append",
        help=(
            "General (non-NSFW) keywords to avoid. "
            "Overrides the default general list when provided."
        ),
    )
    parser.add_argument(
        "--block-keyword-nsfw",
        action="append",
        help=("NSFW/explicit keywords to avoid. Overrides the default NSFW list when provided."),
    )
    parser.add_argument(
        "--block-threshold",
        type=float,
        default=None,
        help=(
            "Threshold on CLIP match probability above which an image is "
            "considered to match a blocked keyword. Higher = blocks fewer images; "
            "lower = blocks more. If set, applies to both general and NSFW keywords."
        ),
    )
    parser.add_argument(
        "--block-threshold-general",
        type=float,
        default=DEFAULT_BLOCK_THRESHOLD_GENERAL,
        help=(
            "Threshold for general (vehicle/war/etc.) keywords "
            f"(default: {DEFAULT_BLOCK_THRESHOLD_GENERAL}). "
            "Higher = blocks fewer images; lower = blocks more."
        ),
    )
    parser.add_argument(
        "--block-threshold-nsfw",
        type=float,
        default=DEFAULT_BLOCK_THRESHOLD_NSFW,
        help=(
            f"Threshold for NSFW/explicit keywords (default: {DEFAULT_BLOCK_THRESHOLD_NSFW}). "
            "Higher = blocks fewer images; lower = blocks more."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print scores; do not copy any files.",
    )
    return parser.parse_args()


def main() -> None:  # pragma: no cover
    args = parse_args()

    # Use explicit block keywords if provided; otherwise fall back to defaults.
    block_keywords: List[str] | None = (
        args.block_keyword if args.block_keyword else args.block_keyword_general
    )
    if block_keywords is None:
        block_keywords = DEFAULT_BLOCK_KEYWORDS_GENERAL

    block_keywords_nsfw: List[str] | None = args.block_keyword_nsfw
    if block_keywords_nsfw is None:
        block_keywords_nsfw = DEFAULT_BLOCK_KEYWORDS_NSFW

    # Support legacy --block-threshold by applying to both lists if provided.
    block_threshold_general = (
        args.block_threshold if args.block_threshold is not None else args.block_threshold_general
    )
    block_threshold_nsfw = (
        args.block_threshold if args.block_threshold is not None else args.block_threshold_nsfw
    )

    filter_wallpapers(
        source_dir=args.source,
        dest_dir=args.dest,
        min_score=args.min_score,
        block_keywords=block_keywords,
        block_threshold=block_threshold_general,
        block_keywords_nsfw=block_keywords_nsfw,
        block_threshold_nsfw=block_threshold_nsfw,
        dry_run=bool(args.dry_run),
    )


if __name__ == "__main__":  # pragma: no cover
    main()
