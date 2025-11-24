# Repository Guidelines

## Project Structure & Module Organization
- Core scripts: `download.py`, `curate.py`, `filter.py` (pipeline steps).
- Shared helpers/config: `wallpaper_common.py`.
- Tests: `tests/` (pytest-based). CI config in `.github/workflows/ci.yml`.
- Optional local config (git-ignored): `wallpipe.toml` in repo root or `~/.config/wallpipe/config.toml`.

## Build, Test, and Development Commands
- Format: `ruff format .`
- Lint: `ruff check .`
- Type check: `pyright`
- Tests: `pytest` (use `pytest --cov` for coverage)
- Run pipeline: \
  `python download.py [download_dir]` → `python curate.py [download_dir] [curated_dir]` → `python filter.py [curated_dir] [dest_dir]`

## Coding Style & Naming Conventions
- Python 3.11, PEP8-ish; line length 100.
- Use `ruff format` + `ruff check` (includes import sorting).
- Type hints encouraged; Pyright “basic” mode. Snake_case for files, variables, and artist slugs.

## Testing Guidelines
- Framework: pytest; coverage target ≥90% (CI uploads to Codecov).
- Tests live in `tests/`, named `test_*.py`, functions `test_*`.
- Prefer temp dirs/monkeypatching; avoid network/real gallery-dl calls in tests.

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
- After changes, run `ruff format`, `ruff check`, `pyright`, `pytest`; include results in the handoff.
- When altering behavior, tooling, or workflow, update both `README.md` and `AGENTS.md` to keep user and contributor docs in sync.
