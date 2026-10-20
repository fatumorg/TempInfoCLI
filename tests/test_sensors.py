from tempinfocli.sensors import Sensor, color_for


def s(kind, v, unit="°C"):
    return Sensor("g", "l", v, unit, kind)


def test_cpu_colors():
    assert color_for(s("cpu", 40)) == "green"
    assert color_for(s("cpu", 80)) == "yellow"
    assert color_for(s("cpu", 95)) == "red"


def test_storage_hotter_sooner():
    assert color_for(s("storage", 60)) == "yellow"
    assert color_for(s("storage", 70)) == "red"
    assert color_for(s("cpu", 60)) == "green"


def test_non_temp_neutral():
    assert color_for(s("fan", 5000, "RPM")) == "cyan"
    assert color_for(s("volt", 12, "V")) == "cyan"
