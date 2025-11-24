# Repository Guidelines

## Project Structure & Module Organization
- Core scripts: `download.py`, `curate.py`, `filter.py` (pipeline steps).
- Shared helpers/config: `common.py`.
- Tests: `tests/` (pytest-based). CI config in `.github/workflows/ci.yml`.
- Optional local config (git-ignored): `wallpipe.toml` in repo root or `~/.config/wallpipe/config.toml`.

## Build, Test, and Development Commands
- Format: `ruff format .`
- Lint: `ruff check .`
- Type check: `pyright`
- Tests: `pytest` (use `pytest --cov` for coverage)
- Run pipeline: \
  `python download.py [download_dir]` → `python curate.py [download_dir] [curated_dir]` → `python filter.py [curated_dir] [dest_dir]`
- Downloader passes `--abort-after 20` to gallery-dl to stop after repeated skips; set `--abort-after 0` to scan everything. Keep README in sync if this default changes.

## Coding Style & Naming Conventions
- Python 3.11, PEP8-ish; line length 100.
- Use `ruff format` + `ruff check` (includes import sorting).
- Type hints encouraged; Pyright “basic” mode. Snake_case for files, variables, and artist slugs.

## Testing Guidelines
- Framework: pytest; coverage target ≥90% (CI uploads to Codecov).
- Tests live in `tests/`, named `test_*.py`, functions `test_*`.
- Prefer temp dirs/monkeypatching; avoid network/real gallery-dl calls in tests.
- Default filters: aesthetics min score 6.0; CLIP keyword block thresholds 0.80 (general) and 0.70 (NSFW) with default blocklists:
  - General: vehicles/war/robots/bikes plus game-asset cues (wireframe/normal map/etc.); NSFW: explicit/sexual terms. Full lists live in `filter.py`; keep README wording aligned if defaults change.
- Threshold semantics: higher = blocks fewer images (more permissive); lower = blocks more (more aggressive). Reflect this wording consistently.
- New features or behavior changes should land with tests (ideally written before or alongside the code).
- Curate supports optional saturation gating (`--skip-bw` / `--min-saturation`); keep docs/tests updated if defaults change.
- Curate supports per-artist fuzzy dedup (`--dedup-hamming` aHash distance); default disabled. Keep README aligned.

## Commit & Pull Request Guidelines
- Commits: concise, present-tense (e.g., “Add CLI defaults for curate”).
- PRs: include summary, testing done (`ruff`, `pyright`, `pytest`), and note behavior changes. Link issues when applicable.
- CI must pass (`ruff check`, `pyright`, `pytest --cov`).

## Security & Configuration Tips
- Do not hardcode personal paths; use `wallpipe.toml` (git-ignored). Env override: `WALLPIPE_CONFIG=/path/to/config`.
- Default paths resolve to `~/Pictures/wallpaper` with `_downloaded`/`_curated` subdirs unless overridden.
- Gallery-dl must be on PATH (CI installs CPU torch and deps).

## Agent-Specific Instructions
- Use `apply_patch` for edits; keep comments minimal and purposeful.
- Before running tooling, check `git diff --name-only` for `.py`/tooling changes.
- Run `uv run ruff format/check`, `uv run pyright`, `uv run pytest` when Python code or tooling (pyproject, CI, requirements) is touched. For doc-only changes, skip these and state “tests not run (docs-only)” in the handoff.
- When lint fixes are needed, prefer `uv run ruff check --fix` to auto-apply safe changes before manual edits.
- When altering behavior, tooling, or workflow, update both `README.md` and `AGENTS.md` to keep user and contributor docs in sync.
- Default artist list: maciej_kuciara now only ArtStation + Behance (DeviantArt inactive); keep examples consistent.
 - Codecov: CI uses Codecov action v5 with GitHub OIDC (no token needed); keep `id-token: write`. Step is `continue-on-error` and posts a PR comment on failure; investigate if uploads fail repeatedly.
