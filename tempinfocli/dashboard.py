import socket
import time

import psutil
from rich.console import Group
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from . import __version__
from .sensors import color_for, limits, usable

_PANELS = (
    ("CPU", ("cpu",), "bright_blue"),
    ("GPU", ("gpu",), "bright_magenta"),
    ("Motherboard", ("mobo",), "bright_cyan"),
    ("Storage", ("storage",), "bright_white"),
    ("Fans / Other", ("fan", "volt", "other"), "bright_black"),
)


def _uptime() -> str:
    s = int(time.time() - psutil.boot_time())
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    return f"{d}d {h}h {s // 60}m"


def _bar(sensor):
    if limits(sensor) is None:
        return Text("")
    hot = limits(sensor)[1]
    color = color_for(sensor)
    return ProgressBar(total=hot, completed=min(max(sensor.value, 0), hot), width=20,
                       complete_style=color, finished_style=color)


def _panel(title: str, items: list, accent: str) -> Panel:
    t = Table.grid(padding=(0, 2), expand=True)
    t.add_column(ratio=1)
    t.add_column(width=20)
    t.add_column(justify="right", width=9)
    for s in items:
        t.add_row(s.label, _bar(s), Text(f"{s.value:.0f} {s.unit}", style=f"bold {color_for(s)}"))
    return Panel(t, title=f"[bold {accent}]{title}[/]", title_align="left", border_style=accent)


def render(sensors: list, interval: float = 1.0):
    sensors = [s for s in sensors if usable(s.value)]
    parts = [Text.assemble(
        ("TempInfoCLI", "bold"),
        (f" v{__version__}", "bold cyan"),
        (f"  ·  {socket.gethostname()}  ·  up {_uptime()}", "dim"),
    )]
    if not sensors:
        parts.append(Panel("no sensors readable on this machine"))
    for title, kinds, accent in _PANELS:
        items = [s for s in sensors if s.kind in kinds]
        if items:
            parts.append(_panel(title, items, accent))
    parts.append(Text(f"refresh {interval:g}s  ·  Ctrl-C to quit", style="dim"))
    return Group(*parts)
