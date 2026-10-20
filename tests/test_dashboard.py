import json

from rich.console import Console

from tempinfocli import cli, dashboard
from tempinfocli.sensors import Sensor


def text(renderable):
    c = Console(width=100, record=True, file=open("/dev/null", "w"))
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


def test_ctrl_c_exits_clean(monkeypatch):
    monkeypatch.setattr(cli, "read_sensors", lambda: [])
    def boom(_):
        raise KeyboardInterrupt
    monkeypatch.setattr(cli.time, "sleep", boom)
    assert cli.main([]) == 0
