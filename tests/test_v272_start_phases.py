from datetime import date
from pathlib import Path

from turnos.scheduler import build_schedule, calendar_dates, is_tt_code, visible_code
from turnos.template_reader import load_template

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "Plantilla_Cuadrantes_Usuarios_v13.xlsx"


def _week(schedule, names, dates, index):
    week = dates[index * 7:(index + 1) * 7]
    return {
        name for name in names
        if any(is_tt_code(schedule[name][d]) for d in week)
    }


def test_template_v12_exposes_start_controls():
    model = load_template(TEMPLATE)
    assert model.calendars["Intensivo"].settings["start_tt_person"] == "Marcos Alba Rocha"
    assert [p.start_phase for p in model.calendars["Rotatorio"].people] == list(range(1, 13))
    assert [p.start_phase for p in model.calendars["EasyVista"].people] == [1, 2, 3]
    assert [p.start_phase for p in model.calendars["Puesto Usuario"].people] == [1, 2, 3]
    assert model.calendars["Farmacia"].settings["first_saturday_person"] == "Sofía Pastor"


def test_intensivo_selected_person_starts_first_tt_of_tape():
    spec = load_template(TEMPLATE).calendars["Intensivo"]
    schedule = build_schedule(spec, 2027, {})
    dates = calendar_dates(2027)
    first_week = dates[:7]
    assert any(is_tt_code(schedule["Marcos Alba Rocha"][d]) for d in first_week)
    assert sum(any(is_tt_code(schedule[n][d]) for d in first_week) for n in spec.names) == 5


def test_easyvista_and_puesto_start_tt_in_selected_order():
    model = load_template(TEMPLATE)
    for key in ("EasyVista", "Puesto Usuario"):
        spec = model.calendars[key]
        schedule = build_schedule(spec, 2027, {})
        dates = calendar_dates(2027)
        for i, person in enumerate(spec.people):
            assert _week(schedule, spec.names, dates, i) == {person.name}


def test_farmacia_selected_person_works_first_saturday():
    spec = load_template(TEMPLATE).calendars["Farmacia"]
    schedule = build_schedule(spec, 2027, {})
    first_sat = date(2027, 1, 2)
    assert visible_code(schedule["Sofía Pastor"][first_sat]) == "F1"
    assert visible_code(schedule["Judit García"][first_sat]) == "D"


def test_sistemas_start_cycle_choices_are_honored():
    spec = load_template(TEMPLATE).calendars["Sistemas"]
    schedule = build_schedule(spec, 2027, {})
    dates = calendar_dates(2027)
    # Luis comienza directamente en TT; Diego en la segunda presencial;
    # Alejandro en la primera presencial.
    assert "Luis Villalobos" in _week(schedule, spec.names, dates, 0)
    assert "Diego Garcia Marcos" in _week(schedule, spec.names, dates, 1)
    assert "Alejandro" in _week(schedule, spec.names, dates, 2)


def test_supervisores_order_tt_by_group_is_honored():
    spec = load_template(TEMPLATE).calendars["Supervisores"]
    schedule = build_schedule(spec, 2027, {})
    dates = calendar_dates(2027)
    # Herramientas de Gestión está configurado 1/2/3.
    assert "Francisco Javier Luis Gonzalez" in _week(schedule, spec.names, dates, 0)
    assert "Roberto Rodriguez Alonso" in _week(schedule, spec.names, dates, 1)
    assert "Fernando Ugidos" in _week(schedule, spec.names, dates, 2)
    # Marian está configurada para la tercera semana y debe tener TT visible.
    assert "Marian Gutierrez García" in _week(schedule, spec.names, dates, 2)
