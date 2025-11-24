from typing import Iterable, Mapping

import download


class DummyCompleted:
    def __init__(self, cmd: list[str]):
        self.cmd = cmd


def test_download_artists_invokes_gallery_dl(tmp_path, monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, check):
        calls.append(cmd)
        return DummyCompleted(cmd)

    monkeypatch.setattr(download.subprocess, "run", fake_run)

    artists: Mapping[str, Iterable[str]] = {"a": ["http://example.com/1", "http://example.com/2"]}
    target = tmp_path / "_dl"
    download.download_artists(artists, download_root=target)

    assert target.is_dir()
    assert len(calls) == 2
    assert all(cmd[0].endswith("gallery-dl") for cmd in calls)
    assert str(target / "a") in calls[0]


def test_download_handles_missing_binary(tmp_path, monkeypatch, capsys):
    def fake_run(cmd, check):
        raise FileNotFoundError("nope")

    monkeypatch.setattr(download.subprocess, "run", fake_run)

    download.download_artists({"a": ["http://example.com"]}, download_root=tmp_path)
    out = capsys.readouterr().out
    assert "gallery-dl" in out and "not found" in out


def test_download_handles_called_process_error(tmp_path, monkeypatch, capsys):
    def fake_run(cmd, check):
        raise download.subprocess.CalledProcessError(3, cmd)

    monkeypatch.setattr(download.subprocess, "run", fake_run)

    download.download_artists({"a": ["http://example.com"]}, download_root=tmp_path)
    out = capsys.readouterr().out
    assert "failed for a" in out
