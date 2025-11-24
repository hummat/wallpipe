import shutil
import subprocess

from download import download_artists, run_gallery_dl


def test_run_gallery_dl_adds_abort(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/gallery-dl")

    captured = {}

    def fake_run(cmd, check):
        captured["cmd"] = cmd
        assert check is True

    monkeypatch.setattr(subprocess, "run", fake_run)

    run_gallery_dl(tmp_path, "http://example.com/foo", abort_after=15)

    assert captured["cmd"][:3] == ["/usr/bin/gallery-dl", "-d", str(tmp_path)]
    assert captured["cmd"][-3:] == ["--abort", "15", "http://example.com/foo"]


def test_run_gallery_dl_allows_disable_abort(monkeypatch, tmp_path):
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/gallery-dl")

    captured = {}

    def fake_run(cmd, check):
        captured["cmd"] = cmd
        assert check is True

    monkeypatch.setattr(subprocess, "run", fake_run)

    run_gallery_dl(tmp_path, "http://example.com/bar", abort_after=0)

    assert "--abort" not in captured["cmd"]
    assert captured["cmd"][-1] == "http://example.com/bar"


def test_download_artists_missing_binary(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    # Should print error and return early
    download_artists({"artist": ["http://example.com/foo"]}, download_root=tmp_path)
    out = capsys.readouterr().out
    assert "gallery-dl` not found" in out


def test_download_artists_calledprocess(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/gallery-dl")

    def fake_run(cmd, check):
        raise subprocess.CalledProcessError(returncode=4, cmd=cmd)

    monkeypatch.setattr(subprocess, "run", fake_run)

    download_artists({"artist": ["http://example.com/foo"]}, download_root=tmp_path)
    out = capsys.readouterr().out
    assert "failed for artist" in out
