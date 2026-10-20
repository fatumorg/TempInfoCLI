"""Rich rendering of sensor readings."""
import socket
import time

import psutil
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .sensors import Sensor, color_for, usable

# panel title -> kinds it shows, in display order
_PANELS = (
    ("CPU", ("cpu",)),
    ("GPU", ("gpu",)),
    ("Motherboard", ("mobo",)),
    ("Storage", ("storage",)),
    ("Fans / Other", ("fan", "volt", "other")),
)


def _uptime() -> str:
    s = int(time.time() - psutil.boot_time())
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    return f"{d}d {h}h {s // 60}m"


def _panel(title: str, items: list) -> Panel:
    t = Table.grid(padding=(0, 2), expand=True)
    t.add_column(ratio=1)
    t.add_column(justify="right")
    for s in items:
        t.add_row(s.label, Text(f"{s.value:.0f} {s.unit}", style=color_for(s)))
    return Panel(t, title=title, title_align="left")


def render(sensors: list, interval: float = 1.0):
    sensors = [s for s in sensors if usable(s.value)]
    parts = [Text(f"{socket.gethostname()}  ·  up {_uptime()}", style="bold")]
    if not sensors:
        parts.append(Panel("no sensors readable on this machine"))
    for title, kinds in _PANELS:
        items = [s for s in sensors if s.kind in kinds]
        if items:
            parts.append(_panel(title, items))
    parts.append(Text(f"refresh {interval:g}s  ·  Ctrl-C to quit", style="dim"))
    return Group(*parts)
