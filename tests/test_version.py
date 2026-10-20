import io
import pathlib

import pytest
from rich.console import Console

from tempinfocli import __version__, cli, dashboard

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["--version"])
    assert e.value.code == 0
    assert capsys.readouterr().out.strip() == f"tempinfocli {__version__}"


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
