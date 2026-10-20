"""Normalized sensor model and per-platform readers."""
from dataclasses import dataclass

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
