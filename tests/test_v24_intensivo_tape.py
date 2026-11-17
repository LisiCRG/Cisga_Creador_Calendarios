from datetime import date, timedelta
from pathlib import Path

from turnos.scheduler import build_schedule, is_tt_code, is_tt_renounced, visible_code, validate_schedule
from turnos.template_reader import load_template

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "Plantilla_Cuadrantes_Usuarios_v13.xlsx"

TAPE = ["TT","P","TT","TT","M","M","M","M","M","TT","P","TT","M","M","M","M","M","M"]


def _weekly_state(schedule, person, monday):
    codes = [schedule[person][monday + timedelta(days=i)] for i in range(5)]
    if any(visible_code(c) == "P" for c in codes):
        return "P"
    if any(is_tt_code(c) for c in codes):
        return "TT"
    return "M1" if any(visible_code(c) == "M1" for c in codes) else "M"


def test_v8_reads_moving_intensivo_tape():
    model = load_template(TEMPLATE)
    spec = model.calendars["Intensivo"]
    assert spec.settings["tape"] == TAPE
    assert spec.settings["max_tt"] == 5
    assert spec.settings["max_p"] == 2
    assert len(spec.people) == len(TAPE) == 18


def test_week_51_matches_reference_tape_and_next_week_moves_down_one_row():
    model = load_template(TEMPLATE)
    spec = model.calendars["Intensivo"]
    # Compatibilidad histórica: sin selector rosa se conserva la ancla v2.4.
    spec.settings["start_tt_person"] = ""
    schedule = build_schedule(spec, 2026, {})
    validate_schedule(spec, schedule, 2026)

    anchor = date(2026, 12, 14)  # semana 51 del cuadrante de referencia
    states = [_weekly_state(schedule, p.name, anchor) for p in spec.people]
    expected_anchor = [
        ("M1" if state == "M" and p.base_shift == "M1" else state)
        for state, p in zip(TAPE, spec.people)
    ]
    assert states == expected_anchor

    next_week = anchor + timedelta(days=7)
    states2 = [_weekly_state(schedule, p.name, next_week) for p in spec.people]
    expected = [TAPE[-1], *TAPE[:-1]]
    # Si un P teórico cae sobre un M1 se verá M1 en lugar de P; aquí las primeras posiciones
    # permiten comprobar el desplazamiento principal sin depender de esa excepción.
    for i, state in enumerate(expected):
        if state in {"M", "P"} and spec.people[i].base_shift == "M1":
            assert states2[i] == "M1"
        else:
            assert states2[i] == state


def test_intensivo_tape_always_has_five_tt_slots_and_at_most_two_real_p():
    model = load_template(TEMPLATE)
    spec = model.calendars["Intensivo"]
    schedule = build_schedule(spec, 2027, {})
    validate_schedule(spec, schedule, 2027)

    monday = date(2026, 12, 28)
    for w in range(18):
        week = monday + timedelta(days=7*w)
        tt = sum(_weekly_state(schedule, p.name, week) == "TT" for p in spec.people)
        p_count = sum(_weekly_state(schedule, p.name, week) == "P" for p in spec.people)
        assert tt == 5
        assert p_count <= 2


def test_m1_suppresses_p_but_keeps_tt_and_angeles_renuncia_is_magenta_logically():
    model = load_template(TEMPLATE)
    spec = model.calendars["Intensivo"]
    schedule = build_schedule(spec, 2027, {})

    m1_names = {"Angeles Lino Martín", "Vanesa Martin", "Carlos Centeno"}
    for name in m1_names:
        assert not any(visible_code(code) == "P" for code in schedule[name].values())

    angeles_codes = list(schedule["Angeles Lino Martín"].values())
    assert any(is_tt_renounced(code) for code in angeles_codes)
