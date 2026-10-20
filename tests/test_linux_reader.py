import os

import pytest

from tempinfocli import sensors

PCI_NAMES = {
    "0000:11:00.0": ("Advanced Micro Devices, Inc. [AMD/ATI]", "Granite Ridge [Radeon 610M]"),
    "0000:03:00.0": ("Advanced Micro Devices, Inc. [AMD/ATI]", "Navi 48 [Radeon RX 9070 XT]"),
    "0000:10:00.0": ("MEDIATEK Corp.", "MT7922 802.11ax PCI Express Wireless Network Adapter"),
}


def write(path, content, mode="w"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode) as f:
        f.write(content)


@pytest.fixture
def sysfs(tmp_path, monkeypatch):
    hwmon = tmp_path / "hwmon"
    devices = tmp_path / "devices"
    hwmon.mkdir()
    monkeypatch.setattr(sensors, "HWMON", str(hwmon))
    monkeypatch.setattr(sensors, "CPUINFO", str(tmp_path / "cpuinfo"))
    monkeypatch.setattr(sensors, "DMI", str(tmp_path / "dmi"))
    monkeypatch.setattr(sensors, "_pci_names", lambda: PCI_NAMES)
    write(str(tmp_path / "cpuinfo"), "processor\t: 0\nmodel name\t: AMD Ryzen 7 9800X3D 8-Core Processor\n")
    write(str(tmp_path / "dmi" / "board_vendor"), "Gigabyte Technology Co., Ltd.\n")
    write(str(tmp_path / "dmi" / "board_name"), "B650 EAGLE\n")

    def chip(n, name, device=None, temps=(), fans=()):
        d = hwmon / f"hwmon{n}"
        write(str(d / "name"), name + "\n")
        if device is not None:
            dev = devices / device
            dev.mkdir(parents=True, exist_ok=True)
            os.symlink(dev, d / "device")
        for i, label, milli in temps:
            write(str(d / f"temp{i}_input"), f"{milli}\n")
            if label:
                write(str(d / f"temp{i}_label"), label + "\n")
        for i, rpm in fans:
            write(str(d / f"fan{i}_input"), f"{rpm}\n")
        return devices / device if device else None

    return chip


def by_label(result):
    return {s.label: s for s in result}


def test_every_device_is_named(sysfs):
    sysfs(0, "k10temp", "0000:00:18.3", temps=[(1, "Tctl", 55250), (2, "Tccd1", 48000)])
    nvme = sysfs(1, "nvme", "0000:02:00.0/nvme/nvme0", temps=[(1, "Composite", 38850)])
    write(str(nvme / "model"), "Lexar SSD NM790 2TB                     \n")
    sysfs(2, "gigabyte_wmi", "PNP0C14:00/wmi", temps=[(1, "", 36000), (2, "", 46000)])
    wifi = sysfs(3, "mt7921_phy0", "0000:10:00.0/ieee80211/phy0", temps=[(1, "", 36000)])
    os.symlink(wifi.parent.parent, wifi / "device")
    sysfs(4, "acpitz", "thermal_zone0", temps=[(1, "", 16800)])

    got = {s.label: (s.kind, s.device, s.value) for s in sensors.read_linux()}

    assert got == {
        "Tctl": ("cpu", "AMD Ryzen 7 9800X3D 8-Core Processor", 55.25),
        "Tccd1": ("cpu", "AMD Ryzen 7 9800X3D 8-Core Processor", 48.0),
        "Composite": ("storage", "Lexar SSD NM790 2TB", 38.85),
        "gigabyte_wmi 1": ("mobo", "Gigabyte B650 EAGLE", 36.0),
        "gigabyte_wmi 2": ("mobo", "Gigabyte B650 EAGLE", 46.0),
        "mt7921_phy0": ("other", "MEDIATEK MT7922 802.11ax PCI Express Wireless Network Adapter", 36.0),
        "acpitz": ("mobo", "Gigabyte B650 EAGLE", 16.8),
    }


def test_amd_igpu_and_dgpu_stay_separate_and_tagged(sysfs):
    igpu = sysfs(0, "amdgpu", "0000:11:00.0", temps=[(1, "edge", 47000)])
    dgpu = sysfs(1, "amdgpu", "0000:03:00.0", temps=[(1, "edge", 61000), (2, "junction", 70000)])
    write(str(igpu / "gpu_metrics"), bytes([120, 0, 2, 1]), "wb")
    write(str(dgpu / "gpu_metrics"), bytes([120, 0, 1, 3]), "wb")

    got = [(s.label, s.device) for s in sensors.read_linux()]

    assert got == [
        ("edge", "AMD Radeon 610M (iGPU)"),
        ("edge", "AMD Radeon RX 9070 XT (dGPU)"),
        ("junction", "AMD Radeon RX 9070 XT (dGPU)"),
    ]


def test_intel_gpu_role_by_slot(tmp_path):
    assert sensors._gpu_role(str(tmp_path / "0000:00:02.0"), "i915") == "iGPU"
    assert sensors._gpu_role(str(tmp_path / "0000:03:00.0"), "i915") == "dGPU"
    assert sensors._gpu_role(str(tmp_path / "0000:01:00.0"), "nouveau") == "dGPU"


def test_unreadable_and_garbage_values_skipped(sysfs, tmp_path):
    sysfs(0, "coretemp", None, temps=[(1, "Core 0", 40000), (2, "Core 1", "N/A")])
    os.mkdir(tmp_path / "hwmon" / "hwmon0" / "temp3_input")
    assert [s.label for s in sensors.read_linux()] == ["Core 0"]


def test_fans_belong_to_their_chip(sysfs):
    sysfs(0, "nct6798", "nct6775.656", fans=[(1, 1200), (2, 0)])
    got = [(s.label, s.unit, s.kind, s.device, s.value) for s in sensors.read_linux()]
    assert got == [
        ("Fan 1", "RPM", "mobo", "Gigabyte B650 EAGLE", 1200.0),
        ("Fan 2", "RPM", "mobo", "Gigabyte B650 EAGLE", 0.0),
    ]


def test_numeric_ordering(sysfs):
    sysfs(0, "coretemp", None, temps=[(i, f"Core {i}", 40000) for i in (1, 2, 10)])
    sysfs(10, "nvme", None, temps=[(1, "Composite", 30000)])
    sysfs(2, "acpitz", None, temps=[(1, "", 20000)])
    assert [s.label for s in sensors.read_linux()] == ["Core 1", "Core 2", "Core 10", "acpitz", "Composite"]


def test_chip_kinds():
    expected = {
        "k10temp": "cpu", "zenpower": "cpu", "coretemp": "cpu",
        "gigabyte_wmi": "mobo", "asus_wmi_sensors": "mobo", "nct6798": "mobo", "it8728": "mobo",
        "amdgpu": "gpu", "i915": "gpu", "GPU die temperature": "gpu",
        "nvme": "storage", "mt7921_phy0": "other",
    }
    assert {chip: sensors._kind_for_chip(chip) for chip in expected} == expected
