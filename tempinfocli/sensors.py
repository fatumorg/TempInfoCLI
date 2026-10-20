import ctypes
import functools
import glob
import math
import os
import re
import subprocess
import sys
from dataclasses import dataclass

HWMON = "/sys/class/hwmon"
CPUINFO = "/proc/cpuinfo"
DMI = "/sys/class/dmi/id"

_THRESHOLDS = {
    "cpu": (75, 90),
    "gpu": (75, 90),
    "mobo": (60, 80),
    "storage": (50, 65),
    "other": (60, 80),
}

_PCI_SLOT = re.compile(r"[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]")


@dataclass
class Sensor:
    group: str
    label: str
    value: float
    unit: str
    kind: str
    device: str = ""


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


def _read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except (OSError, UnicodeDecodeError):
        return None


def _number(path) -> int:
    return int(re.findall(r"\d+", os.path.basename(path))[0])


def _cpu_model():
    match = re.search(r"^model name\s*:\s*(.+)$", _read(CPUINFO) or "", re.M)
    return match[1].strip() if match else None


def _board_name():
    vendor = (_read(os.path.join(DMI, "board_vendor")) or "").split()
    board = _read(os.path.join(DMI, "board_name"))
    if not board:
        return None
    return f"{vendor[0]} {board}" if vendor else board


@functools.lru_cache(maxsize=None)
def _pci_names() -> dict:
    out = _run(["lspci", "-vmm", "-D"]) or ""
    names = {}
    for block in out.split("\n\n"):
        fields = dict(line.split(":\t", 1) for line in block.splitlines() if ":\t" in line)
        if "Slot" in fields:
            names[fields["Slot"]] = (fields.get("Vendor", ""), fields.get("Device", ""))
    return names


def _pci_name(slot):
    if slot not in _pci_names():
        return None
    vendor, device = _pci_names()[slot]
    vendor_tag = re.search(r"\[(.+?)\]", vendor)
    device_tag = re.search(r"\[(.+?)\]", device)
    vendor = vendor_tag[1].split("/")[0] if vendor_tag else vendor.split()[0]
    return f"{vendor} {device_tag[1] if device_tag else device}"


def _pci_slot(dev):
    for path in (dev, os.path.realpath(os.path.join(dev, "device"))):
        if _PCI_SLOT.fullmatch(os.path.basename(path)):
            return os.path.basename(path)
    return None


def _gpu_role(dev, chip) -> str:
    if chip == "amdgpu":
        try:
            with open(os.path.join(dev, "gpu_metrics"), "rb") as f:
                header = f.read(4)
        except OSError:
            return ""
        return {1: "dGPU", 2: "iGPU", 3: "iGPU"}.get(header[2] if len(header) > 2 else None, "")
    if chip == "i915":
        return "iGPU" if os.path.basename(dev) == "0000:00:02.0" else "dGPU"
    if chip == "nouveau":
        return "dGPU"
    return ""


@functools.lru_cache(maxsize=None)
def _describe(dev, chip, kind) -> str:
    if kind == "cpu":
        name = _cpu_model()
    elif kind == "mobo":
        name = _board_name()
    else:
        slot = _pci_slot(dev)
        name = (_read(os.path.join(dev, "model")) or _read(os.path.join(dev, "product_name"))
                or (_pci_name(slot) if slot else None))
    name = name or chip
    role = _gpu_role(dev, chip) if kind == "gpu" else ""
    return f"{name} ({role})" if role else name


def read_linux() -> list:
    out = []
    for hw in sorted(glob.glob(os.path.join(HWMON, "hwmon*")), key=_number):
        chip = _read(os.path.join(hw, "name")) or os.path.basename(hw)
        kind = _kind_for_chip(chip)
        device = _describe(os.path.realpath(os.path.join(hw, "device")), chip, kind)
        for prefix, unit, scale in (("temp", "°C", 1000), ("fan", "RPM", 1)):
            inputs = sorted(glob.glob(os.path.join(hw, f"{prefix}*_input")), key=_number)
            for path in inputs:
                try:
                    value = int(_read(path)) / scale
                except (TypeError, ValueError):
                    continue
                n = _number(path)
                fallback = f"Fan {n}" if prefix == "fan" else (f"{chip} {n}" if len(inputs) > 1 else chip)
                label = _read(os.path.join(hw, f"{prefix}{n}_label")) or fallback
                out.append(Sensor(chip, label, value, unit, kind, device))
    return out


def _run(cmd: list):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


@functools.lru_cache(maxsize=None)
def _nvml():
    if sys.platform == "win32":
        candidates = ["nvml.dll"]
    else:
        candidates = ["libnvidia-ml.so.1", "/run/opengl-driver/lib/libnvidia-ml.so.1"]
    for name in candidates:
        try:
            lib = ctypes.CDLL(name)
        except OSError:
            continue
        if lib.nvmlInit_v2() == 0:
            return lib
    return None


def read_nvidia() -> list:
    lib = _nvml()
    count = ctypes.c_uint()
    if lib is None or lib.nvmlDeviceGetCount_v2(ctypes.byref(count)) != 0:
        return []
    out = []
    for i in range(count.value):
        handle = ctypes.c_void_p()
        name = ctypes.create_string_buffer(96)
        if lib.nvmlDeviceGetHandleByIndex_v2(i, ctypes.byref(handle)) or lib.nvmlDeviceGetName(handle, name, 96):
            continue
        device = f"{name.value.decode(errors='replace')} (dGPU)"
        temp, fan = ctypes.c_uint(), ctypes.c_uint()
        if lib.nvmlDeviceGetTemperature(handle, 0, ctypes.byref(temp)) == 0:
            out.append(Sensor("nvidia", "GPU core", float(temp.value), "°C", "gpu", device))
        if lib.nvmlDeviceGetFanSpeed(handle, ctypes.byref(fan)) == 0:
            out.append(Sensor("nvidia", "Fan", float(fan.value), "%", "gpu", device))
    return out


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
        return read_windows() + read_nvidia()
    return []
