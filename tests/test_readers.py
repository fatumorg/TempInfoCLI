import subprocess
import sys
from types import SimpleNamespace as R

from tempinfocli import sensors


def test_nvidia_parses(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: R(returncode=0, stdout="NVIDIA RTX 4080, 61\n"))
    (s,) = sensors.read_nvidia()
    assert (s.kind, s.value, s.label) == ("gpu", 61.0, "NVIDIA RTX 4080")


def test_nvidia_missing(monkeypatch):
    def boom(*a, **k):
        raise FileNotFoundError
    monkeypatch.setattr(subprocess, "run", boom)
    assert sensors.read_nvidia() == []


def test_windows_error(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: R(returncode=1, stdout=""))
    assert sensors.read_windows() == []
    def boom(*a, **k):
        raise OSError
    monkeypatch.setattr(subprocess, "run", boom)
    assert sensors.read_windows() == []


def test_windows_kelvin(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: R(returncode=0, stdout="3000\n"))
    (s,) = sensors.read_windows()
    assert round(s.value, 2) == 26.85


def test_macos_error(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: R(returncode=1, stdout=""))
    assert sensors.read_macos() == []


def test_dispatch_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(sensors, "read_linux", lambda: ["L"])
    monkeypatch.setattr(sensors, "read_nvidia", lambda: ["N"])
    assert sensors.read_sensors() == ["L", "N"]
