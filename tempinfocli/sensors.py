"""Normalized sensor model and per-platform readers."""
import math
import re
import subprocess
import sys
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


def _run(cmd: list):
    """stdout of a successful external command, else None (absent, failing, or hung)."""
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
    # powermetrics needs root; without it this returns [] (README notes the sudo requirement)
    out = _run(["powermetrics", "--samplers", "smc", "-n", "1"])
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
