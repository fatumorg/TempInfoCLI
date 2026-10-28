import argparse
import dataclasses
import json
import math
import sys
import time

from rich.console import Console
from rich.live import Live

from . import __version__
from .dashboard import render
from .sensors import limits, read_sensors, usable

MIN_INTERVAL = 0.2


def seconds(text):
    value = float(text)
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError("must be a finite number")
    return max(value, MIN_INTERVAL)


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="tempinfo", description="Live terminal temperature dashboard.")
    p.add_argument("--once", action="store_true", help="print one snapshot and exit")
    p.add_argument("--json", action="store_true", help="print sensors as JSON and exit")
    p.add_argument("--stream", action="store_true", help="print one JSON line per refresh, for other programs")
    p.add_argument("--interval", type=seconds, default=1.0, help=f"refresh seconds (min {MIN_INTERVAL})")
    p.add_argument("--no-color", action="store_true", help="disable colors")
    p.add_argument("--version", action="version", version=f"tempinfo {__version__}")
    return p.parse_args(argv)


def record(sensor):
    item = dataclasses.asdict(sensor)
    lim = limits(sensor)
    item["warn"], item["hot"] = lim if lim else (None, None)
    return item


def snapshot():
    return [record(s) for s in read_sensors() if usable(s.value)]


def stream(interval) -> int:
    try:
        while True:
            print(json.dumps({"time": int(time.time() * 1000), "sensors": snapshot()}, ensure_ascii=False), flush=True)
            time.sleep(interval)
    except KeyboardInterrupt:
        return 0
    except BrokenPipeError:
        sys.stdout = None
        return 0


def main(argv=None) -> int:
    a = parse_args(argv)
    console = Console(no_color=a.no_color)
    if a.json:
        print(json.dumps(snapshot(), ensure_ascii=False))
        return 0
    if a.stream:
        return stream(a.interval)
    if a.once or not console.is_terminal:
        console.print(render(read_sensors(), a.interval))
        return 0
    try:
        with Live(render(read_sensors(), a.interval), console=console, screen=True, auto_refresh=False) as live:
            while True:
                time.sleep(a.interval)
                live.update(render(read_sensors(), a.interval), refresh=True)
    except KeyboardInterrupt:
        return 0
