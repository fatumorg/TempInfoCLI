from types import SimpleNamespace as E

import psutil

from tempinfocli import sensors


def test_chips_map_to_kinds(monkeypatch):
    monkeypatch.setattr(psutil, "sensors_temperatures", lambda: {
        "coretemp": [E(label="Package id 0", current=55.0)],
        "nvme": [E(label="Composite", current=40.0)],
    })
    monkeypatch.setattr(psutil, "sensors_fans", lambda: {})
    out = {s.kind: s for s in sensors.read_linux()}
    assert out["cpu"].label == "Package id 0" and out["cpu"].unit == "°C"
    assert out["storage"].label == "Composite"


def test_none_current_skipped(monkeypatch):
    monkeypatch.setattr(psutil, "sensors_temperatures", lambda: {
        "coretemp": [E(label="a", current=None), E(label="b", current=50.0)],
    })
    monkeypatch.setattr(psutil, "sensors_fans", lambda: {})
    assert [s.label for s in sensors.read_linux()] == ["b"]


def test_fans(monkeypatch):
    monkeypatch.setattr(psutil, "sensors_temperatures", lambda: {})
    monkeypatch.setattr(psutil, "sensors_fans", lambda: {"x": [E(label="fan1", current=1200)]})
    (s,) = sensors.read_linux()
    assert (s.kind, s.unit, s.value) == ("fan", "RPM", 1200)
