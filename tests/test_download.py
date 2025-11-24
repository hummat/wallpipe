import shutil
import subprocess

from download import run_gallery_dl


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
