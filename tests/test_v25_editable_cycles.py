from datetime import date, timedelta
from pathlib import Path

from openpyxl import load_workbook

from turnos.models import CalendarSpec, PersonSpec
from turnos.scheduler import build_schedule, calendar_dates, is_tt_code, visible_code
from turnos.template_reader import load_template

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "Plantilla_Cuadrantes_Usuarios_v13.xlsx"


def test_v9_easyvista_cycle_is_read_from_template():
    model = load_template(TEMPLATE)
    spec = model.calendars["EasyVista"]
    assert spec.settings["weekly_cycles"]["M"] == ["BASE", "BASE", "TT"]
    assert spec.settings["weekly_cycles"]["MA"] == ["BASE", "BASE", "TT"]
    assert spec.settings["tt_period"] == 3


def test_easyvista_can_make_one_base_shift_tt_every_week():
    people = [
        PersonSpec("A", base_shift="M", telework="Sí"),
        PersonSpec("B", base_shift="MA", telework="No"),
    ]
    spec = CalendarSpec(
        "EasyVista",
        "EasyVista",
        people,
        {
            "max_tt": 1,
            "tt_period": 3,
            "weekly_cycles": {
                "M": ["TT", "TT", "TT"],
                "MA": ["BASE", "BASE", "BASE"],
            },
            "anchor_monday": "2025-12-29",
        },
    )
    schedule = build_schedule(spec, 2027, {})
    weekdays = [d for d in calendar_dates(2027) if d.weekday() < 5]
    assert all(is_tt_code(schedule["A"][d]) for d in weekdays)
    assert all(not is_tt_code(schedule["B"][d]) for d in weekdays)


def test_easyvista_custom_new_base_shift_works():
    spec = CalendarSpec(
        "EasyVista",
        "EasyVista",
        [PersonSpec("Nueva", base_shift="M2", telework="Sí")],
        {
            "max_tt": 1,
            "tt_period": 3,
            "weekly_cycles": {"M2": ["BASE", "TT", "BASE"]},
            "anchor_monday": "2025-12-29",
        },
    )
    schedule = build_schedule(spec, 2027, {})
    values = list(schedule["Nueva"].values())
    assert any(visible_code(v) == "M2" for v in values)
    assert any(is_tt_code(v) and visible_code(v) == "M2" for v in values)


def test_supervisores_pattern_is_read_and_marian_gets_tt_outside_guard():
    model = load_template(TEMPLATE)
    spec = model.calendars["Supervisores"]
    assert spec.settings["tt_pattern"] == ["BASE", "BASE", "TT"]
    schedule = build_schedule(spec, 2027, {})
    marian = schedule["Marian Gutierrez García"]
    assert any(code == "G" for code in marian.values())
    assert any(is_tt_code(code) for code in marian.values())


def test_v9_editable_cells_are_green():
    wb = load_workbook(TEMPLATE, data_only=False)
    for sheet, cells in {
        "EasyVista": ["B7", "A12", "B12", "D13"],
        "Puesto Usuario": ["B7", "A12", "D13"],
        "Intensivo": ["B14"],
        "Rotatorio": ["A16", "H17"],
        "Supervisores": ["B8", "B14"],
    }.items():
        ws = wb[sheet]
        for addr in cells:
            rgb = ws[addr].fill.fgColor.rgb
            assert rgb in {"FFC6E0B4", "C6E0B4"}, (sheet, addr, rgb)
