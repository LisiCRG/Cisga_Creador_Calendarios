from pathlib import Path

from openpyxl import load_workbook

from turnos.excel_generator import (
    default_general_output_filename,
    default_output_filename,
    generate_excel,
    generate_general_excel,
)
from turnos.scheduler import build_schedule, calendar_dates, validate_schedule
from turnos.template_reader import load_template

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "Plantilla_Cuadrantes_Usuarios_v13.xlsx"


def _generate_selected(tmp_path, keys, holidays=None):
    holidays = holidays or {}
    model = load_template(TEMPLATE)
    generated = []
    for key in keys:
        spec = model.calendars[key]
        schedule = build_schedule(spec, 2027, holidays)
        validate_schedule(spec, schedule, 2027)
        target = tmp_path / default_output_filename(spec, 2027)
        generate_excel(spec, schedule, holidays, 2027, "Castilla y León", "Valladolid", target)
        generated.append((spec, target))
    return generated


def test_general_filename_keeps_e01():
    assert default_general_output_filename(2027) == "Calendario_General_CAU_2027_E01.xlsx"


def test_general_has_one_calendar_sheet_plus_common_auxiliary_sheets(tmp_path):
    generated = _generate_selected(tmp_path, ["Intensivo", "Rotatorio", "Sistemas"])
    target = tmp_path / default_general_output_filename(2027)
    generate_general_excel(generated, 2027, target)

    wb = load_workbook(target, data_only=False)
    assert wb.sheetnames == ["General", "Leyenda", "Organización", "Festivos 2027"]
    wb.close()


def test_general_removes_vacation_columns_and_aligns_calendar_at_column_c(tmp_path):
    generated = _generate_selected(tmp_path, ["Intensivo", "EasyVista", "Rotatorio"])
    target = tmp_path / default_general_output_filename(2027)
    generate_general_excel(generated, 2027, target)

    wb = load_workbook(target, data_only=False)
    ws = wb["General"]
    values = [cell.value for row in ws.iter_rows() for cell in row if cell.value is not None]
    assert "DIAS VAC." not in values
    assert "DISFRUTADOS" not in values
    assert "PENDIENTES" not in values

    # El primer bloque empieza en fila 1: separador + 4 filas de cabecera.
    assert ws["A1"].value == "Intensivo"
    assert ws["A5"].value == "SUBDEPARTAMENTO"
    assert ws["B5"].value == "OPERADOR"
    assert ws["C4"].value == 28  # 28/12/2026, primer día visible de 2027
    assert ws["C5"].value == "L"
    # Todas las columnas de días comparten anchura.
    last_col = 2 + len(calendar_dates(2027))
    widths = {ws.column_dimensions[ws.cell(1, c).column_letter].width for c in range(3, last_col + 1)}
    assert len(widths) == 1
    assert next(iter(widths)) < 5  # anchura compacta equivalente a los individuales
    wb.close()


def test_general_department_separator_is_red_and_bold_through_last_day(tmp_path):
    generated = _generate_selected(tmp_path, ["Intensivo", "Farmacia"])
    target = tmp_path / default_general_output_filename(2027)
    generate_general_excel(generated, 2027, target)

    wb = load_workbook(target, data_only=False)
    ws = wb["General"]
    # Primer departamento en fila 1.
    assert ws["A1"].fill.fgColor.rgb in {"00FF0000", "FFFF0000"}
    assert ws["A1"].font.bold is True
    last_col = 2 + len(calendar_dates(2027))
    assert ws.cell(1, last_col).fill.fgColor.rgb in {"00FF0000", "FFFF0000"}

    # Segundo separador: 1 rojo + 4 cabecera + 18 operadores + 1 blanco = fila 25.
    assert ws["A25"].value == "Farmacia"
    assert ws["A25"].fill.fgColor.rgb in {"00FF0000", "FFFF0000"}
    wb.close()


def test_general_adds_subdepartment_for_ungrouped_and_keeps_real_groups(tmp_path):
    generated = _generate_selected(tmp_path, ["Intensivo", "Sistemas"])
    target = tmp_path / default_general_output_filename(2027)
    generate_general_excel(generated, 2027, target)

    wb = load_workbook(target, data_only=False)
    ws = wb["General"]
    # Intensivo: A6:A23 es un único subdepartamento creado para alinear.
    assert ws["A6"].value == "Intensivo"
    assert "A6:A23" in {str(r) for r in ws.merged_cells.ranges}

    # Sistemas empieza en fila 25; datos desde fila 30. Deben aparecer sus grupos reales.
    group_values = [ws.cell(r, 1).value for r in range(30, 38) if ws.cell(r, 1).value]
    assert set(group_values) >= {"BBDD", "Linux", "Wintel"}
    wb.close()
