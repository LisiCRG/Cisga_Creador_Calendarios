from pathlib import Path

from openpyxl import load_workbook

from turnos.template_reader import load_template
from turnos.scheduler import build_schedule, validate_schedule, visible_code
from turnos.excel_generator import generate_excel

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "Plantilla_Cuadrantes_Usuarios_v13.xlsx"


def test_activo_rotatorio_and_m1_intensivo_and_renuncia():
    model = load_template(TEMPLATE)

    rot = model.calendars["Rotatorio"]
    assert len(rot.people) == 12
    assert "Daniel Ameijeiras" not in rot.names
    assert "Saraid Lozada Garcia" in rot.names

    intensivo = model.calendars["Intensivo"]
    reduced = {p.name for p in intensivo.people if p.reduced or p.base_shift == "M1"}
    assert {"Angeles Lino Martín", "Vanesa Martin", "Carlos Centeno"} <= reduced
    angeles = next(p for p in intensivo.people if p.name == "Angeles Lino Martín")
    assert angeles.telework == "Renuncia"


def test_m1_never_enters_p_even_without_reduced_flag():
    from turnos.models import CalendarSpec, PersonSpec

    people = [
        PersonSpec("M1", base_shift="M1", reduced=False, telework="No"),
        PersonSpec("A", base_shift="M", telework="No"),
    ]
    spec = CalendarSpec("Intensivo", "Intensivo", people, {
        "period_weeks": 9, "max_p": 2, "max_tt": 5, "anchor_monday": "2025-12-29"
    })
    schedule = build_schedule(spec, 2027, {})
    assert not any(visible_code(v) == "P" for v in schedule["M1"].values())
    assert any(visible_code(v) == "M1" for v in schedule["M1"].values())


def test_uniform_teletrabajo_column_in_all_calendars():
    model = load_template(TEMPLATE)
    for key, spec in model.calendars.items():
        assert spec.people
        assert all(p.telework in {"Sí", "Renuncia", "No"} for p in spec.people), key
    # Farmacia conserva su regla de no TT y por defecto queda explícitamente en No.
    assert all(p.telework == "No" for p in model.calendars["Farmacia"].people)


def test_non_intensivo_templates_generate_without_mergedcell_error(tmp_path):
    model = load_template(TEMPLATE)
    for key in ["Rotatorio", "EasyVista", "Puesto Usuario", "Farmacia", "Sistemas", "Supervisores"]:
        spec = model.calendars[key]
        schedule = build_schedule(spec, 2027, {})
        validate_schedule(spec, schedule, 2027)
        target = tmp_path / f"{key}.xlsx"
        generate_excel(spec, schedule, {}, 2027, "Castilla y León", "Valladolid", target)
        assert target.exists() and target.stat().st_size > 0


def test_rotatorio_restores_grouped_vacation_columns(tmp_path):
    model = load_template(TEMPLATE)
    spec = model.calendars["Rotatorio"]
    schedule = build_schedule(spec, 2027, {})
    target = tmp_path / "Rotatorio.xlsx"
    generate_excel(spec, schedule, {}, 2027, "Castilla y León", "Valladolid", target)

    wb = load_workbook(target, data_only=False)
    ws = wb["Rotatorio"]
    merged = {str(r) for r in ws.merged_cells.ranges}
    for row in range(5, 5 + len(spec.people)):
        assert f"B{row}:D{row}" in merged
        assert f"E{row}:G{row}" in merged
        assert f"H{row}:J{row}" in merged
