"""Normalized sensor model and per-platform readers."""
import math
from dataclasses import dataclass

import psutil

# kind -> (warn, hot); kinds absent here are not temperatures
_THRESHOLDS = {
    "cpu": (75, 90),
    "gpu": (75, 90),
    "mobo": (60, 80),
    "storage": (50, 65),
    "other": (60, 80),
}


@dataclass
class Sensor:
    group: str
    label: str
    value: float
    unit: str
    kind: str  # cpu | gpu | mobo | storage | fan | volt | other


def color_for(sensor: Sensor) -> str:
    if sensor.unit != "°C":
        return "cyan"
    warn, hot = _THRESHOLDS.get(sensor.kind, _THRESHOLDS["other"])
    if sensor.value >= hot:
        return "red"
    return "yellow" if sensor.value >= warn else "green"


# chip-name substring -> kind, first match wins
_CHIP_KINDS = (
    ("core", "cpu"), ("k10", "cpu"), ("cpu", "cpu"),
    ("nvme", "storage"), ("drivetemp", "storage"),
    ("amdgpu", "gpu"), ("nouveau", "gpu"),
    ("acpitz", "mobo"), ("mobo", "mobo"),
)


def _kind_for_chip(chip: str) -> str:
    chip = chip.lower()
    return next((k for sub, k in _CHIP_KINDS if sub in chip), "other")


def _valid(x) -> bool:
    return x is not None and not math.isnan(x)


def read_linux() -> list:
    out = []
    # psutil lacks these on some platforms; callers treat a missing API as no sensors
    temps = getattr(psutil, "sensors_temperatures", dict)()
    for chip, entries in temps.items():
        kind = _kind_for_chip(chip)
        for e in entries:
            if _valid(e.current):
                out.append(Sensor(chip, e.label or chip, e.current, "°C", kind))
    for chip, entries in getattr(psutil, "sensors_fans", dict)().items():
        for e in entries:
            if _valid(e.current):
                out.append(Sensor(chip, e.label or chip, e.current, "RPM", "fan"))
    return out
