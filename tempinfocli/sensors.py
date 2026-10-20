import math
import re
import subprocess
import sys
from dataclasses import dataclass

import psutil

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
    kind: str


def limits(sensor: Sensor):
    if sensor.unit != "°C":
        return None
    return _THRESHOLDS.get(sensor.kind, _THRESHOLDS["other"])


def color_for(sensor: Sensor) -> str:
    if limits(sensor) is None:
        return "cyan"
    warn, hot = limits(sensor)
    if sensor.value >= hot:
        return "red"
    return "yellow" if sensor.value >= warn else "green"


_CHIP_KINDS = (
    ("gpu", "gpu"), ("nouveau", "gpu"), ("i915", "gpu"),
    ("core", "cpu"), ("k10", "cpu"), ("zenpower", "cpu"), ("cpu", "cpu"),
    ("nvme", "storage"), ("drivetemp", "storage"),
    ("acpitz", "mobo"), ("mobo", "mobo"), ("wmi", "mobo"), ("nct", "mobo"), ("it8", "mobo"),
)


def _kind_for_chip(chip: str) -> str:
    chip = chip.lower()
    return next((k for sub, k in _CHIP_KINDS if sub in chip), "other")


def usable(x) -> bool:
    return x is not None and not math.isnan(x)


def read_linux() -> list:
    out = []
    readings = [
        (getattr(psutil, "sensors_temperatures", dict)(), "°C", None),
        (getattr(psutil, "sensors_fans", dict)(), "RPM", "fan"),
    ]
    for chips, unit, kind in readings:
        for chip, entries in chips.items():
            for i, e in enumerate(entries, 1):
                if usable(e.current):
                    label = e.label or (f"{chip} {i}" if len(entries) > 1 else chip)
                    out.append(Sensor(chip, label, e.current, unit, kind or _kind_for_chip(chip)))
    return out


def _run(cmd: list):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def read_nvidia() -> list:
    out = _run(["nvidia-smi", "--query-gpu=name,temperature.gpu", "--format=csv,noheader"])
    sensors = []
    for line in (out or "").splitlines():
        name, _, temp = line.rpartition(",")
        try:
            sensors.append(Sensor("nvidia", name.strip(), float(temp), "°C", "gpu"))
        except ValueError:
            continue
    return sensors


def read_macos() -> list:
    out = _run(["powermetrics", "--samplers", "smc", "-n", "1", "-i", "200"])
    return [
        Sensor("smc", m[1].strip(), float(m[2]), "°C", _kind_for_chip(m[1]))
        for m in re.finditer(r"^(.*temperature):\s*([\d.]+) C", out or "", re.M | re.I)
    ]


def read_windows() -> list:
    out = _run(["powershell", "-NoProfile", "-Command",
                "Get-CimInstance -Namespace root/wmi MSAcpi_ThermalZoneTemperature "
                "| ForEach-Object { $_.CurrentTemperature }"])
    sensors = []
    for i, line in enumerate((out or "").split()):
        try:
            sensors.append(Sensor("acpi", f"Thermal zone {i}", float(line) / 10 - 273.15, "°C", "mobo"))
        except ValueError:
            continue
    return sensors


def read_sensors() -> list:
    if sys.platform.startswith("linux"):
        return read_linux() + read_nvidia()
    if sys.platform == "darwin":
        return read_macos()
    if sys.platform == "win32":
        return read_windows()
    return []
