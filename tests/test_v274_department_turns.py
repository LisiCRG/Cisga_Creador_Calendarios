from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "Plantilla_Cuadrantes_Usuarios_v13.xlsx"


def _list_formula(ws, sqref: str) -> str:
    matches = [dv for dv in ws.data_validations.dataValidation if str(dv.sqref) == sqref]
    assert len(matches) == 1, (ws.title, sqref)
    return matches[0].formula1


def test_intensivo_turno_base_has_m_m1_m2():
    wb = load_workbook(TEMPLATE, data_only=False)
    assert _list_formula(wb["Intensivo"], "B26:B43") == '"M,M1,M2"'


def test_easyvista_and_puesto_add_m2_but_not_m1_to_base_dropdown():
    wb = load_workbook(TEMPLATE, data_only=False)
    for sheet in ("EasyVista", "Puesto Usuario"):
        assert _list_formula(wb[sheet], "B17:B19") == '"M,MA,M2"'


def test_sistemas_turno_base_has_m_ma_m1_m2():
    wb = load_workbook(TEMPLATE, data_only=False)
    assert _list_formula(wb["Sistemas"], "C14:C21") == '"M,MA,M1,M2"'


def test_farmacia_standard_template_has_only_f1_f2():
    wb = load_workbook(TEMPLATE, data_only=False)
    ws = wb["Farmacia"]
    assert _list_formula(ws, "B18:B19") == '"F1,F2"'
    codes = [ws[f"A{r}"].value for r in range(24, 27) if ws[f"A{r}"].value]
    assert codes == ["F1", "F2"]


def test_rotatorio_standard_turns_do_not_include_m1_or_m2():
    wb = load_workbook(TEMPLATE, data_only=False)
    ws = wb["Rotatorio"]
    codes = [ws[f"A{r}"].value for r in range(39, 46) if ws[f"A{r}"].value]
    assert codes == ["M", "T", "N", "R", "D"]
    assert "M1" not in codes and "M2" not in codes
