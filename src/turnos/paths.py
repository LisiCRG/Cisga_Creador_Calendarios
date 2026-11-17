from pathlib import Path
import os
import shutil
import sys


def resource_path(relative: str) -> Path:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS"))
    else:
        base = Path(__file__).resolve().parents[2]
    return base / relative


def user_data_dir() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("APPDATA", Path.home()))
        path = root / "GeneradorTurnos"
    else:
        path = Path.home() / ".generador_turnos"
    path.mkdir(parents=True, exist_ok=True)
    return path


def local_holidays_file() -> Path:
    target = user_data_dir() / "local_holidays.json"
    if not target.exists():
        source = resource_path("data/local_holidays.json")
        shutil.copy2(source, target)
    return target


def user_template_file() -> Path:
    return resource_path("templates/Plantilla_Cuadrantes_Usuarios_v13.xlsx")


def type_template_file(calendar_key: str) -> Path:
    mapping = {
        "Intensivo": "Intensivo.xlsx",
        "Rotatorio": "Rotatorio.xlsx",
        "EasyVista": "EasyVista.xlsx",
        "Farmacia": "Farmacia.xlsx",
        "Puesto Usuario": "Puesto_Usuario.xlsx",
        "Sistemas": "Sistemas_Areas_Especializadas.xlsx",
        "Supervisores": "Supervisores_y_OPX.xlsx",
    }
    try:
        return resource_path(f"templates_tipo/{mapping[calendar_key]}")
    except KeyError as exc:
        raise ValueError(f"No hay plantilla tipo para {calendar_key}") from exc


def cisga_logo_file() -> Path:
    return resource_path("assets/cisga_logo.png")


def cisga_icon_file() -> Path:
    return resource_path("assets/cisga.ico")
