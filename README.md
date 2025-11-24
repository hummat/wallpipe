# wallpipe
A small Python pipeline that uses gallery-dl and CLIP-based aesthetic scoring to download, curate, and filter high‑quality landscape wallpapers from selected artists’ online portfolios.

## Configuration
Paths and artists are now configurable via a simple TOML file (no hardcoded usernames or directories). CLI commands now require explicit directories for clarity.

Create `wallpipe.toml` in the repo root **or** `~/.config/wallpipe/config.toml`:

```toml
[paths]
# Defaults to ~/Pictures/wallpaper if omitted
wallpaper_root = "/home/you/Pictures/wallpaper"
# download_root and curated_dir default to subfolders of wallpaper_root if omitted
# download_root = "/home/you/Pictures/wallpaper/downloaded"
# curated_dir  = "/home/you/Pictures/wallpaper/curated"

[artists]
maciej_kuciara = [
  "https://www.artstation.com/maciej",
  "https://www.behance.net/maciejkuciara"
]
# Add or replace artist slugs freely
```

You can also point to a custom config file with `WALLPIPE_CONFIG=/path/to/config.toml`.

## Usage
Run each step; directories default to the current working directory if omitted. Use `uv run` if you manage deps with uv:

```bash
# 1) download raw images into per-artist folders
uv run python download.py         # uses ./downloaded
# or override
uv run python download.py /path/to/downloaded
# downloader stops after 20 consecutive skipped files to avoid long “already downloaded” runs;
# tweak with --abort-after N or disable with --abort-after 0

# 2) curate landscape >=1920x1080 into a flat folder
uv run python curate.py           # uses ./downloaded -> ./curated
# or override
uv run python curate.py /path/to/downloaded /path/to/curated
# optional: drop low-saturation (black/white) images
# uv run python curate.py --skip-bw
# optional: fuzzy dedup by perceptual hash (Hamming distance)
# uv run python curate.py --dedup-hamming 5

# 3) aesthetic filter curated set into another folder
uv run python filter.py           # uses ./curated -> ./filtered
# or override
uv run python filter.py /path/to/curated /path/to/filtered --min-score 6.0
```

## Development
- Preferred (uv):
  - Install deps + venv: `uv sync --group dev`
  - Format: `uv run ruff format .`
  - Lint: `uv run ruff check .`
  - Type check: `uv run pyright`
  - Tests: `uv run pytest` (add `--cov` for coverage)
- Fallback (pip): `pip install -r requirements-dev.txt`; then run commands without `uv run`.
Dev dependencies and runtime deps are declared in `pyproject.toml`; `requirements-dev.txt` mirrors them for pip users.

## Continuous Integration
- GitHub Actions runs on pushes to main/master and all pull requests.
- Steps: `uv sync --group dev`, `uv run ruff check .`, `uv run pyright`, `uv run pytest --cov`; coverage upload to Codecov (OIDC) is best-effort/non-blocking and will comment on PRs if it fails.
- Coverage badge (replace `<owner>` with your GitHub user/org):
  - `![Coverage](https://codecov.io/gh/<owner>/wallpipe/branch/main/graph/badge.svg)`

## Automation Ideas (cron)
You can automate the pipeline with cron on a desktop/server:

- Download monthly (1st of month at 02:00):  
  `0 2 1 * * /path/to/venv/bin/python /path/to/wallpipe/download.py /path/to/downloaded >> /var/log/wallpipe-download.log 2>&1`

- Curate weekly (Sundays at 03:00):  
  `0 3 * * 0 /path/to/venv/bin/python /path/to/wallpipe/curate.py /path/to/downloaded /path/to/curated >> /var/log/wallpipe-curate.log 2>&1`

- Filter weekly (Sundays at 03:30):  
  `30 3 * * 0 /path/to/venv/bin/python /path/to/wallpipe/filter.py /path/to/curated /path/to/filtered --min-score 6.0 >> /var/log/wallpipe-filter.log 2>&1`

### Keyword filtering & thresholds
- Defaults block two buckets:
  - General (vehicles/war/robots/bikes + common game-asset cues like wireframe/normal map) at threshold **0.80**
  - NSFW/explicit terms at threshold **0.70**
  (Full lists live in `filter.py`; override via CLI.)
- Matching uses CLIP text/image similarity with richer prompts (e.g., “explicit photo of …” for NSFW).
- Customize with:
  - `--block-keyword-general foo` / `--block-keyword-nsfw bar`
  - `--block-threshold-general 0.85` / `--block-threshold-nsfw 0.92`
  - Legacy `--block-threshold` still applies one value to both lists.
- Threshold rule of thumb: higher = blocks fewer images (more permissive); lower = blocks more (more aggressive). Calibrate on a small sample via `--dry-run`.
- Aesthetics keep threshold default is **6.0**; change with `--min-score`.
- Curate step can skip low-saturation (B/W) images with `--skip-bw` or a custom `--min-saturation 0.08`.
- Curate can also fuzzy-dedup per artist via `--dedup-hamming N` (aHash distance; try 5–10).

Tips:
- Use absolute paths for Python, repo, and data dirs.
- Ensure the venv has `gallery-dl`, `torch`, `transformers`, `simple-aesthetics-predictor`, `Pillow`.
- Stagger times so curate/filter run after downloads and avoid overlap.
