from pathlib import Path

from openpyxl import load_workbook

from turnos.excel_generator import (
    default_general_output_filename,
    default_output_filename,
    generate_excel,
    generate_general_excel,
)
from turnos.scheduler import build_schedule, validate_schedule
from turnos.template_reader import load_template

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "Plantilla_Cuadrantes_Usuarios_v13.xlsx"


def _generate_selected(tmp_path, keys):
    model = load_template(TEMPLATE)
    generated = []
    for key in keys:
        spec = model.calendars[key]
        schedule = build_schedule(spec, 2027, {})
        validate_schedule(spec, schedule, 2027)
        target = tmp_path / default_output_filename(spec, 2027)
        generate_excel(spec, schedule, {}, 2027, "Castilla y León", "Valladolid", target)
        generated.append((spec, target))
    return generated


def test_general_contains_each_operator_once_and_excludes_rotatorio_ndf_block(tmp_path):
    generated = _generate_selected(tmp_path, ["Rotatorio", "EasyVista"])
    target = tmp_path / default_general_output_filename(2027)
    generate_general_excel(generated, 2027, target)

    wb = load_workbook(target, data_only=False)
    ws = wb["General"]
    model = load_template(TEMPLATE)
    for key in ("Rotatorio", "EasyVista"):
        for person in model.calendars[key].people:
            occurrences = sum(1 for row in ws.iter_rows() for c in row if c.value == person.name)
            assert occurrences == 1

    # El resumen N/D/F de Rotatorio contiene fórmulas; la hoja General no debe
    # heredar ninguna de esas fórmulas ni sus cabeceras mensuales auxiliares.
    formulas = [c.value for row in ws.iter_rows() for c in row if isinstance(c.value, str) and c.value.startswith("=")]
    assert formulas == []
    wb.close()


def test_general_has_one_common_legend_organization_and_holidays(tmp_path):
    generated = _generate_selected(
        tmp_path,
        ["Intensivo", "Rotatorio", "EasyVista", "Farmacia", "Puesto Usuario", "Sistemas", "Supervisores"],
    )
    target = tmp_path / default_general_output_filename(2027)
    generate_general_excel(generated, 2027, target)

    wb = load_workbook(target, data_only=False)
    assert wb.sheetnames.count("General") == 1
    assert wb.sheetnames.count("Leyenda") == 1
    assert wb.sheetnames.count("Organización") == 1
    assert wb.sheetnames.count("Festivos 2027") == 1
    assert not any(name.startswith("_MetaConteo") for name in wb.sheetnames)
    assert "Conteo" not in wb.sheetnames

    ws = wb["Leyenda"]
    rows = []
    for r in range(3, ws.max_row + 1):
        semantic = tuple(ws.cell(r, c).value for c in range(2, 7))
        if any(v not in (None, "") for v in semantic):
            rows.append(semantic)
    assert rows
    assert len(rows) == len(set(rows))

    d_rows = []
    for r in range(3, ws.max_row + 1):
        if ws.cell(r, 2).value == "D":
            d_rows.append((ws.cell(r, 1).value, tuple(ws.cell(r, c).value for c in range(2, 7))))
    assert len(d_rows) >= 2
    assert any("Rotatorio" in str(scope) for scope, _ in d_rows)

    src = load_workbook(generated[0][1], data_only=False)
    src_h = src["Festivos 2027"]
    dst_h = wb["Festivos 2027"]
    assert dst_h["A1"].value == src_h["A1"].value
    assert dst_h["A2"].value == src_h["A2"].value
    assert dst_h["B2"].value == src_h["B2"].value
    src.close()
    wb.close()


def test_general_creates_organization_even_if_selection_has_no_source_sheet(tmp_path):
    generated = _generate_selected(tmp_path, ["Intensivo", "Rotatorio"])
    target = tmp_path / default_general_output_filename(2027)
    generate_general_excel(generated, 2027, target)
    wb = load_workbook(target, data_only=False)
    assert "Organización" in wb.sheetnames
    wb.close()
