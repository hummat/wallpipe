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
# download_root = "/home/you/Pictures/wallpaper/_downloaded"
# curated_dir  = "/home/you/Pictures/wallpaper/_curated"

[artists]
maciej_kuciara = [
  "https://www.artstation.com/maciej",
  "https://www.behance.net/maciejkuciara",
  "https://tiger1313.deviantart.com/"
]
# Add or replace artist slugs freely
```

You can also point to a custom config file with `WALLPIPE_CONFIG=/path/to/config.toml`.

## Usage
Run each step; directories default to the current working directory if omitted:

```bash
# 1) download raw images into per-artist folders
python download.py                # uses ./_downloaded
# or override
python download.py /path/to/_downloaded

# 2) curate landscape >=1920x1080 into a flat folder
python curate.py                  # uses ./_downloaded -> ./_curated
# or override
python curate.py /path/to/_downloaded /path/to/_curated

# 3) aesthetic filter curated set into another folder
python filter.py                  # uses ./_curated -> ./_curated_aesthetic
# or override
python filter.py /path/to/_curated /path/to/_curated_aesthetic --min-score 5.0
```

## Development
- Format: `ruff format .`
- Lint: `ruff check .`
- Type check: `pyright`
- Tests: `pytest`
- Tests with coverage: `pytest --cov`

Dev dependencies are listed in `requirements-dev.txt`.

## Continuous Integration
- GitHub Actions runs on pushes to main/master and all pull requests.
- Steps: install deps (CPU torch), `ruff check .`, `pyright`, `pytest --cov`; coverage uploaded via Codecov using GitHub OIDC (no long-lived token needed; keep `id-token: write` permissions).
- Coverage badge (replace `<owner>` with your GitHub user/org):
  - `![Coverage](https://codecov.io/gh/<owner>/wallpipe/branch/main/graph/badge.svg)`
