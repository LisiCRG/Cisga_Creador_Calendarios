from datetime import date
from pathlib import Path

from turnos.models import HolidayInfo
from turnos.scheduler import build_schedule, visible_code
from turnos.template_reader import load_template


def _model():
    root = Path(__file__).resolve().parents[1]
    return load_template(root / "templates" / "Plantilla_Cuadrantes_Usuarios_v13.xlsx")


def test_local_holiday_is_d_in_all_non_rotating_calendars():
    model = _model()
    d = date(2027, 5, 13)  # jueves
    holidays = {d: HolidayInfo("San Pedro Regalado", "local", ("local",))}

    for key in ("Intensivo", "EasyVista", "Puesto Usuario", "Farmacia", "Sistemas"):
        spec = model.calendars[key]
        schedule = build_schedule(spec, 2027, holidays)
        assert {visible_code(schedule[p.name][d]) for p in spec.people} == {"D"}, key


def test_local_holiday_is_festive_in_rotatorio():
    model = _model()
    spec = model.calendars["Rotatorio"]
    d = date(2027, 5, 13)  # jueves
    holidays = {d: HolidayInfo("San Pedro Regalado", "local", ("local",))}
    schedule = build_schedule(spec, 2027, holidays)

    codes = {visible_code(schedule[p.name][d]) for p in spec.people}
    working_codes = {c for c in codes if c != "D"}
    assert working_codes
    assert all(c.endswith("F") for c in working_codes)


def test_local_holiday_scope_is_recognized_even_when_combined():
    model = _model()
    spec = model.calendars["EasyVista"]
    d = date(2027, 9, 8)
    # Simula una fecha que llega combinada con otro ámbito y mantiene scope local.
    holidays = {d: HolidayInfo("Festivo combinado", "regional", ("regional", "local"))}
    schedule = build_schedule(spec, 2027, holidays)
    assert {visible_code(schedule[p.name][d]) for p in spec.people} == {"D"}
