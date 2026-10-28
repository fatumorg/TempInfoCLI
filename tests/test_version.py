import io
import json
import pathlib

import pytest
from rich.console import Console

from tempinfocli import __version__, cli, dashboard

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["--version"])
    assert e.value.code == 0
    assert capsys.readouterr().out.strip() == f"tempinfo {__version__}"


def test_dashboard_header_shows_version():
    c = Console(width=100, record=True, file=io.StringIO())
    c.print(dashboard.render([]))
    assert f"TempInfoCLI v{__version__}" in c.export_text()


@pytest.mark.parametrize("name, needle", [
    ("default.nix", f'version = "{__version__}";'),
    ("README.md", f"v{__version__}"),
])
def test_version_in_sync(name, needle):
    assert needle in (ROOT / name).read_text(encoding="utf-8")


def test_stream_prints_one_json_line_per_tick(monkeypatch, capsys):
    from tempinfocli.sensors import Sensor
    ticks = []

    def sleep(_):
        ticks.append(1)
        if len(ticks) == 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(cli, "read_sensors", lambda: [Sensor("k10temp", "Tctl", 54.0, "°C", "cpu", "Ryzen"), Sensor("fan", "fan1", 900.0, "RPM", "other")])
    monkeypatch.setattr(cli.time, "sleep", sleep)
    assert cli.main(["--stream", "--interval", "0.2"]) == 0
    lines = capsys.readouterr().out.strip().split("\n")
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert isinstance(first["time"], int)
    assert first["sensors"][0]["warn"] == 75 and first["sensors"][0]["hot"] == 90
    assert first["sensors"][1]["warn"] is None


def test_json_carries_thresholds(monkeypatch, capsys):
    from tempinfocli.sensors import Sensor
    monkeypatch.setattr(cli, "read_sensors", lambda: [Sensor("nvme", "Composite", 41.0, "°C", "storage")])
    assert cli.main(["--json"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["hot"] == 65
