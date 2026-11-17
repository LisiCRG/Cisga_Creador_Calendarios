from datetime import date
from pathlib import Path

from openpyxl import load_workbook

from turnos.excel_generator import STYLES, _style_for_code
from turnos.models import CalendarSpec, PersonSpec
from turnos.scheduler import build_schedule, is_tt_code, visible_code
from turnos.template_reader import load_template

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "Plantilla_Cuadrantes_Usuarios_v13.xlsx"


def test_v10_has_instructions_and_m2_alias():
    wb = load_workbook(TEMPLATE, data_only=False)
    assert "INSTRUCCIONES" in wb.sheetnames
    model = load_template(TEMPLATE)
    assert model.calendars["Intensivo"].settings["shift_aliases"]["M2"] == "M1"
    assert model.calendars["EasyVista"].settings["shift_aliases"]["M2"] == "M1"
    assert model.calendars["Supervisores"].settings["shift_aliases"]["M2"] == "M1"


def test_intensivo_m2_behaves_like_m1_and_never_p():
    people = [PersonSpec(f"P{i:02d}", base_shift=("M2" if i == 0 else "M"), telework="Sí") for i in range(18)]
    tape = ["TT","P","TT","TT","M","M","M","M","M","TT","P","TT","M","M","M","M","M","M"]
    spec = CalendarSpec("Intensivo", "Intensivo", people, {
        "period_weeks": 9, "max_p": 2, "max_tt": 5, "tape": tape,
        "shift_aliases": {"M2":"M1"}, "anchor_tape_monday":"2026-12-14"
    })
    schedule = build_schedule(spec, 2027, {})
    codes = list(schedule["P00"].values())
    assert not any(visible_code(x) == "P" for x in codes)
    assert any(visible_code(x) == "M2" for x in codes)
    assert any(is_tt_code(x) and visible_code(x) == "M2" for x in codes)


def test_easyvista_m2_inherits_m_cycle():
    model = load_template(TEMPLATE)
    spec = model.calendars["EasyVista"]
    spec.people[0].base_shift = "M2"
    schedule = build_schedule(spec, 2027, {})
    vals = list(schedule[spec.people[0].name].values())
    assert any(visible_code(v) == "M2" for v in vals)
    assert any(is_tt_code(v) and visible_code(v) == "M2" for v in vals)


def test_farmacia_custom_shift_can_inherit_f1():
    spec = CalendarSpec("Farmacia", "Farmacia", [
        PersonSpec("A", base_shift="FX", telework="No"),
        PersonSpec("B", base_shift="F2", telework="No"),
    ], {"anchor_saturday":"2026-01-03", "shift_aliases":{"FX":"F1"}})
    schedule = build_schedule(spec, 2026, {})
    assert schedule["A"][date(2026,1,3)] == "FX"
    assert schedule["B"][date(2026,1,3)] == "D"


def test_created_shift_inherits_parent_style():
    assert _style_for_code("X1", {"X1":"M"}) == STYLES["M"]
    assert _style_for_code("Z9", {"Z9":"N"}) == STYLES["N"]


def test_rotatorio_created_night_shift_inherits_n_rules():
    cycle = [("N2",7),("D",8),("M",7),("D",2),("M",7),("D",2),("R",5),("D",4),
             ("N2",7),("D",8),("T",7),("D",2),("T",7),("D",2),("R",5),("D",4)]
    people = [PersonSpec(f"R{i:02d}", telework="Sí") for i in range(12)]
    spec = CalendarSpec("Rotatorio","Rotatorio",people,{"max_r":2,"cycle":cycle,"anchor_night":"2025-12-31","shift_aliases":{"N2":"N"}})
    schedule = build_schedule(spec, 2026, {})
    assert any(visible_code(v).startswith("N2") for v in schedule["R00"].values())


def test_sistemas_m2_and_supervisores_m2_keep_visible_code():
    sistemas = CalendarSpec("Sistemas","Sistemas",[
        PersonSpec("S", group="W", base_shift="M2", tt_pattern="Siempre TT", telework="Sí")
    ], {"tt_period":3,"anchor_monday":"2025-12-29","shift_aliases":{"M2":"M1","M1":"M"}})
    ss = build_schedule(sistemas, 2027, {})
    assert any(is_tt_code(v) and visible_code(v) == "M2" for v in ss["S"].values())

    supervisors = CalendarSpec("Supervisores","Supervisores",[
        PersonSpec("Sup", group="G", base_shift="M2", telework="Sí")
    ], {"tt_period":3,"tt_pattern":["BASE","BASE","TT"],"anchor_monday":"2025-12-29","guard_anchor":"2025-12-29","shift_aliases":{"M2":"M1","M1":"M"}}, group_tt_limits={"G":1})
    sc = build_schedule(supervisors, 2027, {})
    assert any(visible_code(v) == "M2" for v in sc["Sup"].values())
    assert any(is_tt_code(v) and visible_code(v) == "M2" for v in sc["Sup"].values())
