import io
import json

import pytest

from rich.console import Console

from tempinfocli import cli, dashboard
from tempinfocli.sensors import Sensor


def text(renderable):
    c = Console(width=100, record=True, file=io.StringIO())
    c.print(renderable)
    return c.export_text()


def test_empty_state():
    assert "no sensors readable" in text(dashboard.render([]))


def test_groups_and_nan_filtered():
    out = text(dashboard.render([
        Sensor("coretemp", "Package", 50.0, "°C", "cpu"),
        Sensor("nvidia", "RTX", 61.0, "°C", "gpu"),
        Sensor("coretemp", "Bad", float("nan"), "°C", "cpu"),
    ]))
    assert "CPU" in out and "GPU" in out and "Package" in out and "RTX" in out
    assert "Bad" not in out and "nan" not in out.lower()


def test_all_nan_is_empty_state():
    assert "no sensors readable" in text(dashboard.render([Sensor("a", "b", float("nan"), "°C", "cpu")]))


def test_interval_clamped():
    assert cli.parse_args(["--interval", "0"]).interval == cli.MIN_INTERVAL
    assert cli.parse_args(["--interval", "-3"]).interval == cli.MIN_INTERVAL
    assert cli.parse_args(["--interval", "2"]).interval == 2


def test_once(monkeypatch, capsys):
    monkeypatch.setattr(cli, "read_sensors", lambda: [Sensor("c", "Package", 50.0, "°C", "cpu")])
    assert cli.main(["--once"]) == 0
    assert "Package" in capsys.readouterr().out


def test_json(monkeypatch, capsys):
    monkeypatch.setattr(cli, "read_sensors", lambda: [
        Sensor("c", "P", 50.0, "°C", "cpu"), Sensor("c", "Bad", float("nan"), "°C", "cpu")])
    assert cli.main(["--json"]) == 0
    assert [d["label"] for d in json.loads(capsys.readouterr().out)] == ["P"]


@pytest.mark.parametrize("bad", ["nan", "inf", "abc"])
def test_interval_rejects_non_finite(bad):
    with pytest.raises(SystemExit):
        cli.parse_args(["--interval", bad])


def test_non_terminal_prints_once(monkeypatch, capsys):
    monkeypatch.setattr(cli, "read_sensors", lambda: [Sensor("c", "Package", 50.0, "°C", "cpu")])
    monkeypatch.setattr(cli.time, "sleep", lambda _: pytest.fail("live loop on a non-terminal"))
    assert cli.main([]) == 0
    assert "Package" in capsys.readouterr().out


def test_ctrl_c_exits_clean(monkeypatch):
    monkeypatch.setattr(cli, "read_sensors", lambda: [])
    monkeypatch.setattr(cli, "Console", lambda **k: Console(force_terminal=True, file=io.StringIO(), **k))
    def boom(_):
        raise KeyboardInterrupt
    monkeypatch.setattr(cli.time, "sleep", boom)
    assert cli.main([]) == 0


def test_temperature_rows_get_headroom_bar_fans_do_not():
    out = text(dashboard.render([
        Sensor("c", "Package", 45.0, "°C", "cpu"),
        Sensor("f", "fan1", 1200.0, "RPM", "fan"),
    ]))
    package = next(line for line in out.splitlines() if "Package" in line)
    fan = next(line for line in out.splitlines() if "fan1" in line)
    assert "━" in package and "━" not in fan


def test_one_panel_per_device_with_igpu_and_dgpu():
    out = text(dashboard.render([
        Sensor("amdgpu", "edge", 47.0, "°C", "gpu", "AMD Radeon 610M (iGPU)"),
        Sensor("nvidia", "GPU core", 44.0, "°C", "gpu", "NVIDIA GeForce RTX 5070 Ti (dGPU)"),
        Sensor("nvidia", "Fan", 30.0, "%", "gpu", "NVIDIA GeForce RTX 5070 Ti (dGPU)"),
    ]))
    assert "GPU · AMD Radeon 610M (iGPU)" in out
    assert "GPU · NVIDIA GeForce RTX 5070 Ti (dGPU)" in out
    assert out.index("AMD Radeon 610M") < out.index("edge") < out.index("RTX 5070 Ti") < out.index("GPU core")


def test_names_are_not_rich_markup():
    out = text(dashboard.render([Sensor("x", "[bold]odd[/bold]", 40.0, "°C", "other", "Weird [AMD/ATI] thing")]))
    assert "[bold]odd[/bold]" in out and "Weird [AMD/ATI] thing" in out
