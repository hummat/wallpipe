# Contributing to wallpipe

Thanks for your interest in contributing! This document covers development setup and guidelines.

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- gallery-dl on PATH

### Quick Start

```bash
# Clone the repository
git clone https://github.com/hummat/wallpipe.git
cd wallpipe

# Install development dependencies
uv sync --group dev

# Run all checks
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest --cov
```

## Code Style

- Python 3.11+
- 100-character line limit
- Type hints encouraged; pyright "basic" mode
- Run `ruff format` + `ruff check` (includes import sorting)

## Architecture

The pipeline consists of three steps:
1. `download.py` — fetch wallpapers via gallery-dl
2. `curate.py` — organize and deduplicate
3. `filter.py` — aesthetic scoring and content filtering

Configuration via `wallpipe.toml` (git-ignored) or `~/.config/wallpipe/config.toml`.

## Pull Request Process

1. **Create an issue first** for non-trivial changes
2. **Fork and branch** from `main`
3. **Make your changes** following the style guide
4. **Run all checks** — `ruff check`, `pyright`, `pytest --cov`
5. **Update documentation** if behavior changes (README.md, AGENTS.md)
6. **Submit PR** using the template

### Commit Messages

- Use present tense: "Add feature" not "Added feature"
- Keep the first line under 72 characters
- Reference issues: "Fix filter threshold (#42)"

## Testing

- Framework: pytest; coverage target ≥90%
- Prefer temp dirs/monkeypatching; avoid network calls in tests
- New features should land with tests

## Questions?

- Open a [Discussion](https://github.com/hummat/wallpipe/discussions) for questions
- Check existing [Issues](https://github.com/hummat/wallpipe/issues) for known problems
