from pathlib import Path

from openpyxl import load_workbook

from turnos.excel_generator import generate_excel
from turnos.scheduler import build_schedule, calendar_dates, is_tt_code, validate_schedule
from turnos.template_reader import load_template

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "Plantilla_Cuadrantes_Usuarios_v13.xlsx"


def test_intensivo_template_v8_uses_five_tt_and_fits_18_people():
    model = load_template(TEMPLATE)
    spec = model.calendars["Intensivo"]
    assert spec.settings["max_tt"] == 5
    assert len(spec.people) == 18
    assert len(spec.settings["tape"]) == 18
    assert spec.settings["tape"].count("TT") == 5
    assert spec.settings["tape"].count("P") == 2

    schedule = build_schedule(spec, 2027, {})
    validate_schedule(spec, schedule, 2027)


def test_group_headers_are_horizontal_in_grouped_outputs(tmp_path):
    model = load_template(TEMPLATE)
    for key, sheet_name in [
        ("EasyVista", "Easyvista"),
        ("Puesto Usuario", "PuestoUsuario"),
        ("Sistemas", "SistemasEspecializados"),
        ("Supervisores", "Supervisores_OPX"),
    ]:
        spec = model.calendars[key]
        schedule = build_schedule(spec, 2027, {})
        validate_schedule(spec, schedule, 2027)
        target = tmp_path / f"{key}.xlsx"
        generate_excel(spec, schedule, {}, 2027, "Castilla y León", "Valladolid", target)

        wb = load_workbook(target, data_only=False)
        ws = wb[sheet_name]
        group_merges = [
            rng for rng in ws.merged_cells.ranges
            if rng.min_col == 1 and rng.max_col == 1 and rng.min_row >= 5
        ]
        assert group_merges, key
        for rng in group_merges:
            cell = ws.cell(rng.min_row, 1)
            assert cell.alignment.textRotation in (0, None), (key, str(rng), cell.alignment.textRotation)
        assert (ws.column_dimensions["A"].width or 0) >= 20


def test_rotatorio_has_visible_blank_row_before_ndf(tmp_path):
    model = load_template(TEMPLATE)
    spec = model.calendars["Rotatorio"]
    schedule = build_schedule(spec, 2027, {})
    validate_schedule(spec, schedule, 2027)
    target = tmp_path / "Rotatorio.xlsx"
    generate_excel(spec, schedule, {}, 2027, "Castilla y León", "Valladolid", target)

    wb = load_workbook(target, data_only=False)
    ws = wb["Rotatorio"]
    blank_row = 5 + len(spec.people)
    ndf_row = blank_row + 1

    assert ws.row_dimensions[blank_row].hidden is not True
    assert all(ws.cell(blank_row, c).value in (None, "") for c in range(1, 11))
    assert any(ws.cell(ndf_row, c).value not in (None, "") for c in range(2, 11))
