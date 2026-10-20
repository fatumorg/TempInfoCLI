import ctypes
import subprocess
import sys
from types import SimpleNamespace as R

from tempinfocli import sensors

NVML_ERROR_NOT_SUPPORTED = 3


class FakeNVML:
    def __init__(self, gpus):
        self.gpus = gpus

    def nvmlDeviceGetCount_v2(self, count):
        count._obj.value = len(self.gpus)
        return 0

    def nvmlDeviceGetHandleByIndex_v2(self, index, handle):
        handle._obj.value = index + 1
        return 0

    def nvmlDeviceGetName(self, handle, buf, size):
        buf.value = self.gpus[handle.value - 1]["name"]
        return 0

    def _put(self, handle, key, out):
        value = self.gpus[handle.value - 1].get(key)
        if value is None:
            return NVML_ERROR_NOT_SUPPORTED
        out._obj.value = value
        return 0

    def nvmlDeviceGetTemperature(self, handle, sensor, out):
        return self._put(handle, "temp", out)

    def nvmlDeviceGetFanSpeed(self, handle, out):
        return self._put(handle, "fan", out)


def test_nvidia_via_nvml(monkeypatch):
    monkeypatch.setattr(sensors, "_nvml", lambda: FakeNVML([{"name": b"NVIDIA GeForce RTX 5070 Ti", "temp": 44, "fan": 30}]))
    got = [(s.label, s.value, s.unit, s.kind, s.device) for s in sensors.read_nvidia()]
    assert got == [
        ("GPU core", 44.0, "°C", "gpu", "NVIDIA GeForce RTX 5070 Ti (dGPU)"),
        ("Fan", 30.0, "%", "gpu", "NVIDIA GeForce RTX 5070 Ti (dGPU)"),
    ]


def test_nvidia_unsupported_readings_skipped(monkeypatch):
    monkeypatch.setattr(sensors, "_nvml", lambda: FakeNVML([{"name": b"Tesla T4", "temp": 50}]))
    assert [s.label for s in sensors.read_nvidia()] == ["GPU core"]


def test_nvidia_without_driver(monkeypatch):
    monkeypatch.setattr(sensors, "_nvml", lambda: None)
    assert sensors.read_nvidia() == []


def test_nvml_load_failure_is_none(monkeypatch):
    sensors._nvml.cache_clear()
    def missing(name):
        raise OSError(name)
    monkeypatch.setattr(ctypes, "CDLL", missing)
    try:
        assert sensors._nvml() is None
    finally:
        sensors._nvml.cache_clear()


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


def test_dispatch(monkeypatch):
    monkeypatch.setattr(sensors, "read_linux", lambda: ["L"])
    monkeypatch.setattr(sensors, "read_windows", lambda: ["W"])
    monkeypatch.setattr(sensors, "read_nvidia", lambda: ["N"])
    monkeypatch.setattr(sys, "platform", "linux")
    assert sensors.read_sensors() == ["L", "N"]
    monkeypatch.setattr(sys, "platform", "win32")
    assert sensors.read_sensors() == ["W", "N"]
