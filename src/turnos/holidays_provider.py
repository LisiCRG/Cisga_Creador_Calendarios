from __future__ import annotations

from datetime import date
import json
from pathlib import Path
from typing import Dict, Iterable, List

from .models import HolidayInfo
from .paths import local_holidays_file

FESTIVOS_LOCALES_ESPERADOS = 2

COMUNIDADES = {
    "Andalucía": "AN", "Aragón": "AR", "Asturias": "AS", "Canarias": "CN",
    "Cantabria": "CB", "Castilla y León": "CL", "Castilla-La Mancha": "CM",
    "Cataluña": "CT", "Ceuta": "CE", "Comunidad de Madrid": "MD",
    "Comunidad Valenciana": "VC", "Extremadura": "EX", "Galicia": "GA",
    "Islas Baleares": "IB", "La Rioja": "RI", "Melilla": "ML", "Murcia": "MC",
    "Navarra": "NC", "País Vasco": "PV",
}


class MissingLocalHolidaysError(ValueError):
    pass


class HolidayProviderError(RuntimeError):
    pass


def _load_holidays_lib():
    try:
        import holidays  # type: ignore
        return holidays
    except ImportError as exc:
        raise HolidayProviderError(
            "No está instalado el paquete 'holidays'. Ejecuta pip install -r requirements.txt"
        ) from exc


def load_local_database(path: Path | None = None) -> dict:
    path = path or local_holidays_file()
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_local_database(data: dict, path: Path | None = None) -> None:
    path = path or local_holidays_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)


def cities_in_database(path: Path | None = None) -> List[str]:
    return sorted(load_local_database(path).keys())


def get_local_entries(city: str, year: int, path: Path | None = None) -> List[dict]:
    db = load_local_database(path)
    return list(db.get(city.strip(), {}).get(str(year), []))


def set_local_entries(city: str, year: int, entries: List[dict], path: Path | None = None) -> None:
    city = city.strip()
    if not city:
        raise ValueError("La ciudad no puede estar vacía.")
    db = load_local_database(path)
    db.setdefault(city, {})[str(year)] = entries
    save_local_database(db, path)


def validate_local_entries(city: str, year: int, path: Path | None = None) -> List[dict]:
    entries = get_local_entries(city, year, path)
    if len(entries) < FESTIVOS_LOCALES_ESPERADOS:
        raise MissingLocalHolidaysError(
            f"{city} {year}: hay {len(entries)} festivo(s) local(es) configurado(s) y "
            f"se esperan al menos {FESTIVOS_LOCALES_ESPERADOS}."
        )
    for item in entries:
        d = date.fromisoformat(item["date"])
        if d.year != year:
            raise MissingLocalHolidaysError(
                f"El festivo local '{item.get('name', '')}' tiene año {d.year}, no {year}."
            )
    return entries


def _spain_calendar(holidays_module, years: Iterable[int], subdiv: str | None = None):
    """Construye el calendario de España con nombres en español cuando es posible.

    En ejecutables PyInstaller antiguos podía faltar el catálogo gettext de
    ``python-holidays`` y aparecer:

        [Errno 2] No translation file found for domain: 'ES'

    La release incluye ahora los recursos de ``holidays`` en el ``.spec``.
    Aun así mantenemos un fallback sin ``language="es"`` para que una
    ausencia accidental de catálogos de traducción no impida validar ni
    generar los cuadrantes.
    """
    kwargs = {"years": list(years)}
    if subdiv:
        kwargs["subdiv"] = subdiv

    try:
        return holidays_module.Spain(language="es", **kwargs)
    except (TypeError, FileNotFoundError, OSError):
        return holidays_module.Spain(**kwargs)


def _add_configurable_december_holiday(
    result: Dict[date, HolidayInfo],
    d: date,
    name: str,
) -> None:
    """Añade un festivo opcional de empresa sin alterar festivos ya existentes."""
    if d in result:
        old = result[d]
        scopes = tuple(dict.fromkeys((*old.scopes, old.kind, "custom")))
        result[d] = HolidayInfo(old.name, old.kind, scopes)
    else:
        result[d] = HolidayInfo(name, "custom", ("custom",))


def build_holiday_calendar(
    year: int,
    community: str,
    city: str,
    *,
    include_adjacent_years: bool = True,
    require_local_for_target_year: bool = True,
    dec24_holiday: bool = False,
    dec31_holiday: bool = False,
) -> Dict[date, HolidayInfo]:
    if community not in COMUNIDADES:
        raise ValueError(f"Comunidad no soportada: {community}")
    if not city.strip():
        raise ValueError("Debes indicar una ciudad.")

    if require_local_for_target_year:
        validate_local_entries(city, year)

    years = [year - 1, year, year + 1] if include_adjacent_years else [year]
    hlib = _load_holidays_lib()
    national = _spain_calendar(hlib, years)
    regional = _spain_calendar(hlib, years, COMUNIDADES[community])

    result: Dict[date, HolidayInfo] = {}
    for d, name in national.items():
        result[d] = HolidayInfo(str(name), "national", ("national",))
    for d, name in regional.items():
        if d not in result:
            result[d] = HolidayInfo(str(name), "regional", ("regional",))
        else:
            old = result[d]
            scopes = tuple(dict.fromkeys((*old.scopes, old.kind, "regional")))
            result[d] = HolidayInfo(old.name, old.kind, scopes)

    for y in years:
        for item in get_local_entries(city, y):
            d = date.fromisoformat(item["date"])
            local_name = item.get("name") or "Festivo local"
            if d in result:
                old = result[d]
                scopes = tuple(dict.fromkeys((*old.scopes, old.kind, "local")))
                result[d] = HolidayInfo(f"{old.name} / {local_name}", "local", scopes)
            else:
                result[d] = HolidayInfo(local_name, "local", ("local",))

    # 24/12 y 31/12 son festivos opcionales de empresa seleccionados en la GUI.
    # Se aplican también a los años adyacentes porque el cuadrante muestra semanas
    # completas que pueden incluir días de diciembre del año anterior/siguiente.
    for y in years:
        if dec24_holiday:
            _add_configurable_december_holiday(result, date(y, 12, 24), "24 de diciembre")
        if dec31_holiday:
            _add_configurable_december_holiday(result, date(y, 12, 31), "31 de diciembre")
    return result
