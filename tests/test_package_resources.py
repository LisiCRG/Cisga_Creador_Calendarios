from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_user_template_is_bundled():
    assert (ROOT / "templates" / "Plantilla_Cuadrantes_Usuarios_v13.xlsx").exists()


def test_seven_type_templates_are_bundled():
    expected = {
        "Intensivo.xlsx", "Rotatorio.xlsx", "EasyVista.xlsx", "Farmacia.xlsx",
        "Puesto_Usuario.xlsx", "Sistemas_Areas_Especializadas.xlsx", "Supervisores_y_OPX.xlsx",
    }
    actual = {p.name for p in (ROOT / "templates_tipo").glob("*.xlsx")}
    assert expected == actual
