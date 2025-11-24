import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def reload_wallpaper_common():
    """
    Helper to reload module with fresh caches.
    Ensures repo root is on sys.path so the module is importable.
    """
    sys.modules.pop("wallpaper_common", None)
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    return importlib.import_module("wallpaper_common")


def test_is_image_file_extensions():
    wc = reload_wallpaper_common()
    assert wc.is_image_file(Path("a.jpg"))
    assert wc.is_image_file(Path("a.png"))
    assert wc.is_image_file(Path("a.webp"))
    assert wc.is_image_file(Path("a.JPEG"))
    assert wc.is_image_file(Path("a.txt")) is False


def test_env_config_overrides_repo_and_home(monkeypatch, tmp_path):
    # create repo config and home config that should be ignored
    repo_cfg = Path(__file__).parent.parent / "wallpipe.toml"
    repo_cfg.write_text('[paths]\nwallpaper_root = "/tmp/should_not_use"\n')
    home_cfg_dir = tmp_path / ".config" / "wallpipe"
    home_cfg_dir.mkdir(parents=True)
    home_cfg = home_cfg_dir / "config.toml"
    home_cfg.write_text('[paths]\nwallpaper_root = "/tmp/should_not_use2"\n')

    custom_cfg = tmp_path / "custom.toml"
    custom_root = tmp_path / "env_root"
    custom_cfg.write_text(f'[paths]\nwallpaper_root = "{custom_root}"\n')

    monkeypatch.setenv("WALLPIPE_CONFIG", str(custom_cfg))
    # ensure home lookup points to our temp dir
    monkeypatch.setenv("HOME", str(tmp_path))

    wc = reload_wallpaper_common()
    assert wc.WALLPAPER_ROOT == custom_root


def test_defaults_when_no_config(monkeypatch):
    # ensure no env config is set
    monkeypatch.delenv("WALLPIPE_CONFIG", raising=False)
    # ensure repo/home configs do not exist for this test
    repo_cfg = Path(__file__).parent.parent / "wallpipe.toml"
    if repo_cfg.exists():
        repo_cfg.unlink()

    wc = reload_wallpaper_common()
    assert wc.WALLPAPER_ROOT == wc.DEFAULT_WALLPAPER_ROOT
    assert wc.DOWNLOAD_ROOT == wc.DEFAULT_DOWNLOAD_ROOT
    assert wc.CURATED_DIR == wc.DEFAULT_CURATED_DIR


def test_resolve_paths_uses_config_when_no_overrides(tmp_path, monkeypatch):
    cfg = tmp_path / "config.toml"
    custom_root = tmp_path / "wp_root"
    cfg.write_text(
        "[paths]\n"
        f'wallpaper_root = "{custom_root}"\n'
        f'download_root = "{custom_root / "_dl"}"\n'
        f'curated_dir = "{custom_root / "_cur"}"\n'
    )

    monkeypatch.setenv("WALLPIPE_CONFIG", str(cfg))

    wc = reload_wallpaper_common()

    assert wc.WALLPAPER_ROOT == custom_root
    assert wc.DOWNLOAD_ROOT == custom_root / "_dl"
    assert wc.CURATED_DIR == custom_root / "_cur"


def test_resolve_paths_allows_overrides(tmp_path, monkeypatch):
    monkeypatch.delenv("WALLPIPE_CONFIG", raising=False)
    wc = reload_wallpaper_common()

    override_root = tmp_path / "root"
    paths = wc.resolve_paths(
        wallpaper_root=override_root,
        download_root=override_root / "dl",
        curated_dir=override_root / "cur",
    )

    assert paths["wallpaper_root"] == override_root
    assert paths["download_root"] == override_root / "dl"
    assert paths["curated_dir"] == override_root / "cur"
