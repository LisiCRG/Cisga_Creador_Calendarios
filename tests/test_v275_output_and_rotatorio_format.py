from pathlib import Path

from openpyxl import load_workbook

from turnos.catalog import CALENDAR_KEYS, OUTPUT_BASENAMES
from turnos.excel_generator import default_output_filename, generate_excel
from turnos.scheduler import build_schedule, validate_schedule
from turnos.template_reader import load_template

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "Plantilla_Cuadrantes_Usuarios_v13.xlsx"


def _rgb(cell):
    color = cell.fill.fgColor
    return (color.rgb or "")[-6:].upper() if color.type == "rgb" else ""


def test_all_generated_names_end_in_e01():
    model = load_template(TEMPLATE)
    for key in CALENDAR_KEYS:
        assert OUTPUT_BASENAMES[key].endswith("_{year}_E01.xlsx")
        assert default_output_filename(model.calendars[key], 2027).endswith("_2027_E01.xlsx")


def test_rotatorio_spacer_is_unformatted_and_ndf_people_are_banded(tmp_path):
    model = load_template(TEMPLATE)
    spec = model.calendars["Rotatorio"]
    schedule = build_schedule(spec, 2027, {})
    validate_schedule(spec, schedule, 2027)
    target = tmp_path / "Calendario_Rotatorio_2027_E01.xlsx"
    generate_excel(spec, schedule, {}, 2027, "Castilla y León", "Valladolid", target)

    wb = load_workbook(target, data_only=False)
    ws = wb["Rotatorio"]

    blank_row = 5 + len(spec.people)
    top = blank_row + 1
    first_data = top + 2
    second_data = first_data + 1

    # La línea entre Saraid/último agente y el bloque N/D/F no debe conservar
    # ni rellenos ni bordes, tampoco en la zona del calendario.
    for c in range(1, ws.max_column + 1):
        cell = ws.cell(blank_row, c)
        assert cell.value in (None, "")
        assert cell.fill.fill_type is None
        assert all(side.style is None for side in (cell.border.left, cell.border.right, cell.border.top, cell.border.bottom))

    # Francisco (primera persona de cada bloque N/D/F) sí debe estar formateado.
    assert ws.cell(first_data, 1).value == spec.people[0].name
    assert _rgb(ws.cell(first_data, 1)) == "FFF2CC"
    for c in range(2, 11):
        assert _rgb(ws.cell(first_data, c)) == "FFF2CC"
        assert ws.cell(first_data, c).font.bold is True

    # La segunda fila conserva el alternado gris, sin depender de dónde caiga
    # el bloque dentro de la plantilla tipo.
    assert _rgb(ws.cell(second_data, 1)) == "D9D9D9"
    for c in range(2, 11):
        assert _rgb(ws.cell(second_data, c)) == "D9D9D9"
