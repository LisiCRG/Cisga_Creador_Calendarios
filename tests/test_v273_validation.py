from pathlib import Path
import shutil

import pytest
from openpyxl import load_workbook

from turnos.template_reader import TemplateValidationError, load_template

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "Plantilla_Cuadrantes_Usuarios_v13.xlsx"


def _mutated_template(tmp_path: Path, sheet: str, changes: dict[str, object]) -> Path:
    target = tmp_path / "plantilla.xlsx"
    shutil.copy2(TEMPLATE, target)
    wb = load_workbook(target)
    ws = wb[sheet]
    for cell, value in changes.items():
        ws[cell] = value
    wb.save(target)
    return target


@pytest.mark.parametrize(
    ("sheet", "cell", "value"),
    [
        ("Rotatorio", "D22", "COSARARA"),
        ("EasyVista", "E17", "COSARARA"),
        ("Puesto Usuario", "E17", "TT semana 99"),
        ("Sistemas", "G15", "COSARARA"),
        ("Supervisores", "F27", "COSARARA"),
    ],
)
def test_invalid_manual_start_value_is_not_silently_ignored(tmp_path, sheet, cell, value):
    path = _mutated_template(tmp_path, sheet, {cell: value})
    with pytest.raises(TemplateValidationError):
        load_template(path)


def test_intensivo_start_person_must_have_tt_enabled(tmp_path):
    path = _mutated_template(tmp_path, "Intensivo", {"C26": "No"})
    with pytest.raises(TemplateValidationError, match="Teletrabajo=No"):
        load_template(path)


@pytest.mark.parametrize("sheet", ["EasyVista", "Puesto Usuario"])
def test_weekly_start_tt_rejected_when_telework_is_no(tmp_path, sheet):
    path = _mutated_template(tmp_path, sheet, {"C17": "No"})
    with pytest.raises(TemplateValidationError, match="Teletrabajo=No"):
        load_template(path)


def test_sistemas_start_only_applies_to_cyclic_pattern(tmp_path):
    path = _mutated_template(tmp_path, "Sistemas", {"G14": "Semana TT"})
    with pytest.raises(TemplateValidationError, match="solo se aplica"):
        load_template(path)


def test_sistemas_start_rejected_when_telework_is_no(tmp_path):
    path = _mutated_template(tmp_path, "Sistemas", {"E15": "No"})
    with pytest.raises(TemplateValidationError, match="Teletrabajo=No"):
        load_template(path)


def test_supervisor_order_rejected_when_telework_is_no(tmp_path):
    path = _mutated_template(tmp_path, "Supervisores", {"D27": "No"})
    with pytest.raises(TemplateValidationError, match="Teletrabajo=No"):
        load_template(path)


def test_farmacia_start_person_must_be_active(tmp_path):
    path = _mutated_template(tmp_path, "Farmacia", {"B10": "Persona inexistente"})
    with pytest.raises(TemplateValidationError, match="no está activa"):
        load_template(path)


def test_start_dropdowns_use_stop_validation_and_allow_blank():
    wb = load_workbook(TEMPLATE)
    expected = {
        "Intensivo": "B12",
        "Rotatorio": "D22:D34",
        "EasyVista": "E17:E19",
        "Puesto Usuario": "E17:E19",
        "Farmacia": "B10",
        "Sistemas": "G14:G21",
        "Supervisores": "F27:F41",
    }
    for sheet, sqref in expected.items():
        matches = [dv for dv in wb[sheet].data_validations.dataValidation if str(dv.sqref) == sqref]
        assert len(matches) == 1, (sheet, sqref)
        dv = matches[0]
        assert dv.showErrorMessage is True
        assert dv.errorStyle == "stop"
        assert dv.allowBlank is True
