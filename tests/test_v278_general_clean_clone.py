from pathlib import Path
from copy import copy

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


def test_general_has_both_reference_legends_and_holidays(tmp_path):
    generated = _generate_selected(
        tmp_path,
        ["Intensivo", "Rotatorio", "EasyVista", "Farmacia", "Puesto Usuario", "Sistemas", "Supervisores"],
    )
    target = tmp_path / default_general_output_filename(2027)
    generate_general_excel(generated, 2027, target)

    wb = load_workbook(target, data_only=False)
    assert wb.sheetnames.count("General") == 1
    assert wb.sheetnames.count("Leyenda") == 1
    assert wb.sheetnames.count("LeyendaROTATORIO") == 1
    assert "Organización" not in wb.sheetnames
    assert wb.sheetnames.count("Festivos 2027") == 1
    assert not any(name.startswith("_MetaConteo") for name in wb.sheetnames)
    assert "Conteo" not in wb.sheetnames

    # Ambas referencias del General son idénticas a las de los individuales.
    for title, source_idx in (("Leyenda", 0), ("LeyendaROTATORIO", 1)):
        individual = load_workbook(generated[source_idx][1])
        expected = individual[title]
        actual = wb[title]
        assert actual.max_row == expected.max_row
        assert actual.max_column == expected.max_column
        for row in expected.iter_rows():
            for cell in row:
                other = actual[cell.coordinate]
                assert other.value == cell.value
                for attr in ("font", "fill", "border", "alignment", "number_format"):
                    assert copy(getattr(other, attr)) == copy(getattr(cell, attr))
        assert {k: v.width for k, v in actual.column_dimensions.items()} == {k: v.width for k, v in expected.column_dimensions.items()}
        assert {k: v.height for k, v in actual.row_dimensions.items()} == {k: v.height for k, v in expected.row_dimensions.items()}
        individual.close()

    src = load_workbook(generated[0][1], data_only=False)
    src_h = src["Festivos 2027"]
    dst_h = wb["Festivos 2027"]
    assert dst_h["A1"].value == src_h["A1"].value
    assert dst_h["A2"].value == src_h["A2"].value
    assert dst_h["B2"].value == src_h["B2"].value
    src.close()
    wb.close()


def test_general_does_not_create_organization(tmp_path):
    generated = _generate_selected(tmp_path, ["Intensivo", "Rotatorio"])
    target = tmp_path / default_general_output_filename(2027)
    generate_general_excel(generated, 2027, target)
    wb = load_workbook(target, data_only=False)
    assert "Organización" not in wb.sheetnames
    wb.close()


def test_general_always_has_both_legends_even_without_rotatorio(tmp_path):
    generated = _generate_selected(tmp_path, ["Farmacia"])
    target = tmp_path / default_general_output_filename(2027)
    generate_general_excel(generated, 2027, target)
    wb = load_workbook(target)
    assert wb.sheetnames == ["General", "Leyenda", "LeyendaROTATORIO", "Festivos 2027"]
    assert wb["Leyenda"]["E11"].value == "Teletrabajo"
    assert wb["LeyendaROTATORIO"]["C18"].value == "Teletrabajo"
    wb.close()
