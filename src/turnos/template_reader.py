from __future__ import annotations

from pathlib import Path
import re
import unicodedata
from typing import Iterable, List, Tuple

from openpyxl import load_workbook

from .catalog import CALENDAR_KEYS, DISPLAY_NAMES, REQUIRED_SHEETS
from .models import CalendarSpec, LegendRow, PersonSpec, TemplateModel


class TemplateValidationError(ValueError):
    pass


def _norm(value: object) -> str:
    text = "" if value is None else str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).casefold()


def _yes_no_tt(value: object) -> str:
    n = _norm(value)
    if n in {"si", "sí", "s", "yes"}:
        return "Sí"
    if n in {"renuncia", "no tt", "no teletrabajo"}:
        return "Renuncia"
    if n in {"no", "no aplica", "ninguno", ""}:
        return "No"
    raise TemplateValidationError(f"Valor de Teletrabajo no reconocido: {value!r}")


def _yes_no(value: object) -> bool:
    n = _norm(value)
    if n in {"si", "sí", "s", "yes"}:
        return True
    if n in {"no", "n", ""}:
        return False
    raise TemplateValidationError(f"Valor Sí/No no reconocido: {value!r}")


def _find_cell(ws, label: str, *, startswith: bool = False) -> Tuple[int, int]:
    target = _norm(label)
    for row in ws.iter_rows():
        for cell in row:
            current = _norm(cell.value)
            if (startswith and current.startswith(target)) or (not startswith and current == target):
                return cell.row, cell.column
    raise TemplateValidationError(f"{ws.title}: no se ha encontrado la etiqueta '{label}'.")


def _value_right(ws, label: str) -> object:
    r, c = _find_cell(ws, label)
    return ws.cell(r, c + 1).value


def _as_int(value: object, label: str) -> int:
    try:
        result = int(value)
    except Exception as exc:
        raise TemplateValidationError(f"{label}: se esperaba un número entero y se encontró {value!r}.") from exc
    if result < 0:
        raise TemplateValidationError(f"{label}: no puede ser negativo.")
    return result




def _phase_number(value: object, label: str, maximum: int) -> int | None:
    """Lee una fase 1..N usando únicamente formatos conocidos.

    Se aceptan números puros (``3``), etiquetas de semana
    (``TT semana 3`` / ``Semana 3``) y fases de Rotatorio
    (``F03 · C1 Mañana 1``). Un texto que simplemente contenga un número
    ya no se interpreta como fase: así un valor pegado manualmente no puede
    pasar silenciosamente por válido.
    """
    raw = str(value or "").strip()
    if not raw:
        return None

    normalized = _norm(raw)
    patterns = (
        r"^0*(\d{1,2})$",
        r"^(?:fase\s*)0*(\d{1,2})$",
        r"^(?:tt\s+)?semana\s+0*(\d{1,2})$",
        r"^f\s*0*(\d{1,2})(?:\s+.*)?$",
    )
    match = next((re.fullmatch(pattern, normalized) for pattern in patterns if re.fullmatch(pattern, normalized)), None)
    if not match:
        raise TemplateValidationError(f"{label}: valor no reconocido {value!r}. Selecciona una opción del desplegable.")

    number = int(match.group(1))
    if not 1 <= number <= maximum:
        raise TemplateValidationError(f"{label}: la fase debe estar entre 1 y {maximum}; se encontró {number}.")
    return number


def _system_start_phase(value: object) -> int | None:
    raw = _norm(value)
    if not raw:
        return None
    mapping = {
        "1a semana sin tt": 1,
        "1 semana sin tt": 1,
        "primera semana sin tt": 1,
        "2a semana sin tt": 2,
        "2 semana sin tt": 2,
        "segunda semana sin tt": 2,
        "semana tt": 3,
        "tt": 3,
        "1": 1,
        "2": 2,
        "3": 3,
    }
    if raw not in mapping:
        raise TemplateValidationError(
            f"Sistemas · Inicio ciclo TT: valor no reconocido {value!r}. Selecciona una opción del desplegable."
        )
    return mapping[raw]


def _people_table_has_headers(
    ws,
    headers: List[str],
    *,
    after_label: str = "PERSONAS",
) -> bool:
    """Indica si una tabla contiene exactamente las columnas de una versión.

    Se usa para compatibilidad hacia atrás sin ocultar errores de contenido:
    solo se hace *fallback* cuando falta una columna antigua/nueva, nunca
    cuando una celda existente contiene un valor inválido.
    """
    try:
        section_row, _ = _find_cell(ws, after_label, startswith=True)
        _find_header_row(ws, headers, after_row=section_row + 1)
        return True
    except TemplateValidationError:
        return False

def _find_header_row(ws, required_headers: Iterable[str], *, after_row: int = 1) -> Tuple[int, dict[str, int]]:
    wanted = {_norm(h): h for h in required_headers}
    for r in range(after_row, ws.max_row + 1):
        row_map = {}
        for c in range(1, ws.max_column + 1):
            n = _norm(ws.cell(r, c).value)
            if n in wanted:
                row_map[wanted[n]] = c
        if len(row_map) == len(wanted):
            return r, row_map
    raise TemplateValidationError(
        f"{ws.title}: no se ha encontrado la cabecera con columnas {', '.join(required_headers)}."
    )


def _read_people_table(
    ws,
    headers: List[str],
    *,
    after_label: str = "PERSONAS",
    max_blank_rows: int = 2,
) -> List[dict[str, object]]:
    section_row, _ = _find_cell(ws, after_label, startswith=True)
    header_row, cols = _find_header_row(ws, headers, after_row=section_row + 1)
    result: List[dict[str, object]] = []
    blank_run = 0
    for r in range(header_row + 1, ws.max_row + 1):
        name_col = cols.get("Nombre")
        name = ws.cell(r, name_col).value if name_col else None
        if not str(name or "").strip():
            blank_run += 1
            if blank_run >= max_blank_rows:
                break
            continue
        blank_run = 0
        item = {h: ws.cell(r, c).value for h, c in cols.items()}
        result.append(item)
    return result


def _read_people_table_active(
    ws,
    headers: List[str],
    *,
    after_label: str = "PERSONAS",
) -> List[dict[str, object]]:
    """Lee una tabla de personas.

    La columna ``Activo`` es compatible hacia atrás: si no existe, todas las
    filas se consideran activas. Si existe, las filas con Activo=No se
    conservan en la plantilla pero se excluyen del calendario generado.
    """
    try:
        rows = _read_people_table(ws, [*headers, "Activo"], after_label=after_label)
    except TemplateValidationError:
        rows = _read_people_table(ws, headers, after_label=after_label)
        for row in rows:
            row["Activo"] = "Sí"
    return [row for row in rows if _yes_no(row.get("Activo", "Sí"))]


def _read_legend(ws) -> List[LegendRow]:
    try:
        label_row, label_col = _find_cell(ws, "LEYENDA")
    except TemplateValidationError:
        return []
    header_row = label_row + 1
    start_col = label_col
    max_cols = min(5, ws.max_column - start_col + 1)
    out: List[LegendRow] = []
    blank = 0
    for r in range(header_row + 1, min(ws.max_row, header_row + 40) + 1):
        vals = [ws.cell(r, start_col + c).value for c in range(max_cols)]
        if not any(v not in (None, "") for v in vals):
            blank += 1
            if blank >= 2:
                break
            continue
        blank = 0
        out.append(LegendRow(["" if v is None else str(v) for v in vals]))
    return out


def _parse_cycle_cell(value: object) -> tuple[str, int]:
    text = str(value or "").strip().replace("x", "×").replace("X", "×")
    match = re.match(r"^\s*([A-Za-z0-9]+)\s*×\s*(\d+)\s*$", text)
    if not match:
        raise TemplateValidationError(f"Bloque de ciclo no reconocido: {value!r}. Use, por ejemplo, 'N × 7'.")
    return match.group(1).upper(), int(match.group(2))


def _read_rotatorio_cycles(ws) -> List[tuple[str, int]]:
    r, _ = _find_cell(ws, "CICLO POR DÍAS", startswith=True)
    header_row = None
    for rr in range(r + 1, min(ws.max_row, r + 8) + 1):
        if _norm(ws.cell(rr, 1).value).startswith("bloque 1"):
            header_row = rr
            break
    if header_row is None:
        raise TemplateValidationError("Rotatorio: no se ha encontrado la fila 'Bloque 1'.")
    cycles: List[tuple[str, int]] = []
    for rr in (header_row + 1, header_row + 2):
        for c in range(1, ws.max_column + 1):
            value = ws.cell(rr, c).value
            if value not in (None, ""):
                cycles.append(_parse_cycle_cell(value))
    if not cycles:
        raise TemplateValidationError("Rotatorio: el ciclo está vacío.")
    return cycles


def _read_intensivo_tape(ws) -> list[str]:
    """Lee la cinta circular del Intensivo desde una sola celda editable.

    Formato recomendado en plantilla::
        TT,P,TT,TT,M,M,M,M,M,TT,P,TT,M,M,M,M,M,M

    Se aceptan T o TT como sinónimos de Teletrabajo.
    """
    raw = str(_value_right(ws, "Cinta de rotación") or "").strip()
    if not raw:
        raise TemplateValidationError("Intensivo: la Cinta de rotación está vacía.")
    parts = [x.strip().upper() for x in re.split(r"[,;|]+", raw) if x.strip()]
    normalized = ["TT" if x in {"T", "TT"} else x for x in parts]
    invalid = [x for x in normalized if x not in {"M", "P", "TT"}]
    if invalid:
        raise TemplateValidationError(
            "Intensivo: la cinta solo admite M, P y TT. Valores no válidos: " + ", ".join(invalid)
        )
    return normalized


def _normalize_cycle_token(value: object, base: str) -> str:
    text = str(value or "").strip().upper()
    if not text:
        raise TemplateValidationError(f"Ciclo de {base}: hay una semana vacía.")
    if text in {"T", "TELETRABAJO"}:
        text = "TT"
    if text == base.upper() or text == "BASE":
        return "BASE"
    return text


def _read_weekly_cycle_table(ws) -> tuple[dict[str, list[str]], int]:
    """Lee un ciclo semanal editable del bloque ``CICLO POR SEMANAS``.

    Cada fila representa un Turno base. Las columnas ``Semana 1..N`` pueden
    contener el propio código/base, ``BASE``, ``TT``, ``D`` u otro código de
    turno visible. Esto permite editar ciclos e incorporar nuevos turnos sin
    tocar Python: basta añadir una fila antes de la sección PERSONAS.
    """
    section_row, _ = _find_cell(ws, "CICLO POR SEMANAS", startswith=True)
    header_row, cols = _find_header_row(ws, ["Turno base"], after_row=section_row + 1)
    base_col = cols["Turno base"]
    week_cols = []
    for c in range(base_col + 1, ws.max_column + 1):
        if _norm(ws.cell(header_row, c).value).startswith("semana"):
            week_cols.append(c)
        elif week_cols:
            break
    if not week_cols:
        raise TemplateValidationError(f"{ws.title}: el ciclo semanal no tiene columnas Semana 1..N.")

    cycles: dict[str, list[str]] = {}
    for r in range(header_row + 1, ws.max_row + 1):
        first = str(ws.cell(r, base_col).value or "").strip()
        if not first:
            break
        if _norm(first).startswith("personas"):
            break
        base = first.upper()
        if base in cycles:
            raise TemplateValidationError(f"{ws.title}: el turno base {base!r} está repetido en CICLO POR SEMANAS.")
        cycles[base] = [_normalize_cycle_token(ws.cell(r, c).value, base) for c in week_cols]
    if not cycles:
        raise TemplateValidationError(f"{ws.title}: no hay turnos definidos en CICLO POR SEMANAS.")
    return cycles, len(week_cols)


def _read_csv_pattern(value: object, label: str) -> list[str]:
    raw = str(value or "").strip()
    if not raw:
        raise TemplateValidationError(f"{label}: el patrón está vacío.")
    parts = [x.strip().upper() for x in re.split(r"[,;|]+", raw) if x.strip()]
    normalized = []
    for token in parts:
        if token in {"T", "TELETRABAJO"}:
            token = "TT"
        normalized.append(token)
    return normalized


def _read_group_limits(ws) -> dict[str, int]:
    try:
        r, _ = _find_cell(ws, "MÁXIMO TT POR GRUPO", startswith=True)
    except TemplateValidationError:
        return {}
    header_row, cols = _find_header_row(ws, ["Grupo", "Máximo TT simultáneo"], after_row=r + 1)
    out: dict[str, int] = {}
    for rr in range(header_row + 1, ws.max_row + 1):
        group = str(ws.cell(rr, cols["Grupo"]).value or "").strip()
        if not group:
            break
        out[group] = _as_int(ws.cell(rr, cols["Máximo TT simultáneo"]).value, f"{group} máximo TT")
    return out


def _read_guard_order(ws) -> List[str]:
    try:
        r, _ = _find_cell(ws, "ROTACIÓN DE GUARDIA", startswith=True)
    except TemplateValidationError:
        return []
    header_row, cols = _find_header_row(ws, ["Orden", "Supervisor"], after_row=r + 1)
    values = []
    for rr in range(header_row + 1, ws.max_row + 1):
        name = str(ws.cell(rr, cols["Supervisor"]).value or "").strip()
        if not name:
            break
        order = _as_int(ws.cell(rr, cols["Orden"]).value, "Orden de Guardia")
        values.append((order, name))
    return [name for _, name in sorted(values)]




def _read_shift_aliases(ws) -> dict[str, str]:
    """Lee TURNOS CREADOS: Código nuevo -> Se comporta como.

    Permite crear códigos visibles nuevos sin modificar Python. El código
    hereda las reglas funcionales del turno indicado en ``Se comporta como``.
    """
    try:
        section_row, _ = _find_cell(ws, "TURNOS", startswith=True)
    except TemplateValidationError:
        return {}
    header_row, cols = _find_header_row(ws, ["Se comporta como"], after_row=section_row + 1)
    parent_col = cols["Se comporta como"]
    code_col = parent_col - 1
    aliases: dict[str, str] = {}
    for r in range(header_row + 1, ws.max_row + 1):
        code = str(ws.cell(r, code_col).value or "").strip().upper()
        parent = str(ws.cell(r, parent_col).value or "").strip().upper()
        if not code:
            break
        # Parent vacío = turno nativo/listado para selección; no crea alias.
        if not parent:
            continue
        if code == parent:
            raise TemplateValidationError(f"{ws.title}: el turno {code!r} no puede comportarse como sí mismo.")
        aliases[code] = parent
    # Detecta ciclos simples en alias.
    for code in aliases:
        seen = {code}
        cur = aliases.get(code)
        while cur in aliases:
            if cur in seen:
                raise TemplateValidationError(f"{ws.title}: hay un ciclo en TURNOS CREADOS alrededor de {code!r}.")
            seen.add(cur)
            cur = aliases.get(cur)
    return aliases


def _legend_with_aliases(ws, aliases: dict[str, str]) -> List[LegendRow]:
    legend = _read_legend(ws)
    existing = {str(row.values[0]).strip().upper() for row in legend if row.values}
    for code, parent in aliases.items():
        if code not in existing:
            legend.append(LegendRow([code, f"Turno creado (como {parent})", "Reglas heredadas", "Color heredado", code]))
    return legend


def _calendar_intensivo(ws) -> CalendarSpec:
    aliases = _read_shift_aliases(ws)
    # v2.7: Turno base es explícito (M/M1/M2/código creado). Compatibilidad con plantillas antiguas.
    if _people_table_has_headers(ws, ["Nombre", "Turno base", "Teletrabajo"]):
        rows = _read_people_table_active(ws, ["Nombre", "Turno base", "Teletrabajo"])
        people = [
            PersonSpec(
                name=str(x["Nombre"]).strip(),
                reduced=False,
                telework=_yes_no_tt(x["Teletrabajo"]),
                base_shift=str(x["Turno base"] or "M").strip().upper(),
            ) for x in rows
        ]
    else:
        rows = _read_people_table_active(ws, ["Nombre", "Reducción", "Teletrabajo"])
        people = [
            PersonSpec(
                name=str(x["Nombre"]).strip(),
                reduced=_yes_no(x["Reducción"]),
                telework=_yes_no_tt(x["Teletrabajo"]),
                base_shift="M1" if _yes_no(x["Reducción"]) else "M",
            ) for x in rows
        ]
    settings = {
        "period_weeks": _as_int(_value_right(ws, "Semanas entre P"), "Semanas entre P"),
        "max_p": _as_int(_value_right(ws, "Máximo P en la misma semana"), "Máximo P"),
        "max_tt": _as_int(_value_right(ws, "Máximo TT en la misma semana"), "Máximo TT"),
        "tape": _read_intensivo_tape(ws),
        "start_tt_person": str(_value_right(ws, "Inicio cinta · 1ª posición TT") or "").strip(),
        "shift_aliases": aliases,
        "anchor_tape_monday": "2026-12-14",
        "anchor_monday": "2025-12-29",
    }
    return CalendarSpec("Intensivo", DISPLAY_NAMES["Intensivo"], people, settings, _legend_with_aliases(ws, aliases))


def _calendar_rotatorio(ws) -> CalendarSpec:
    aliases = _read_shift_aliases(ws)
    if _people_table_has_headers(ws, ["Nombre", "Teletrabajo", "Inicio ciclo"]):
        rows = _read_people_table_active(ws, ["Nombre", "Teletrabajo", "Inicio ciclo"])
        people = [
            PersonSpec(
                str(x["Nombre"]).strip(),
                telework=_yes_no_tt(x["Teletrabajo"]),
                start_phase=_phase_number(x.get("Inicio ciclo"), "Rotatorio · Inicio ciclo", 12),
            )
            for x in rows
        ]
    else:
        rows = _read_people_table_active(ws, ["Nombre", "Teletrabajo"])
        people = [PersonSpec(str(x["Nombre"]).strip(), telework=_yes_no_tt(x["Teletrabajo"])) for x in rows]
    settings = {
        "max_r": _as_int(_value_right(ws, "Refuerzos simultáneos"), "Refuerzos simultáneos"),
        "cycle": _read_rotatorio_cycles(ws),
        "shift_aliases": aliases,
        "night_start_weekday": 2,
        "anchor_night": "2025-12-31",
    }
    return CalendarSpec("Rotatorio", DISPLAY_NAMES["Rotatorio"], people, settings, _legend_with_aliases(ws, aliases))


def _calendar_easy_or_puesto(ws, key: str, default_group: str) -> CalendarSpec:
    aliases = _read_shift_aliases(ws)
    if _people_table_has_headers(ws, ["Nombre", "Turno base", "Teletrabajo", "Inicio TT"]):
        rows = _read_people_table_active(ws, ["Nombre", "Turno base", "Teletrabajo", "Inicio TT"])
        people = [
            PersonSpec(
                name=str(x["Nombre"]).strip(), group=default_group,
                base_shift=str(x["Turno base"] or "M").strip().upper(),
                telework=_yes_no_tt(x["Teletrabajo"]),
                start_phase=_phase_number(x.get("Inicio TT"), f"{DISPLAY_NAMES[key]} · Inicio TT", 12),
            ) for x in rows
        ]
    else:
        rows = _read_people_table_active(ws, ["Nombre", "Turno base", "Teletrabajo"])
        people = [
            PersonSpec(
                name=str(x["Nombre"]).strip(), group=default_group,
                base_shift=str(x["Turno base"] or "M").strip().upper(),
                telework=_yes_no_tt(x["Teletrabajo"]),
            ) for x in rows
        ]
    cycles, period = _read_weekly_cycle_table(ws)
    def has_cycle(base: str) -> bool:
        cur = base
        seen = set()
        while cur not in cycles and cur in aliases and cur not in seen:
            seen.add(cur); cur = aliases[cur]
        return cur in cycles
    missing = sorted({p.base_shift for p in people if not has_cycle(p.base_shift)})
    if missing:
        raise TemplateValidationError(
            f"{DISPLAY_NAMES[key]}: faltan ciclos o alias para los turnos base: {', '.join(missing)}."
        )
    settings = {
        "max_tt": _as_int(_value_right(ws, "Máximo TT por semana"), "Máximo TT por semana"),
        "tt_period": period, "weekly_cycles": cycles, "shift_aliases": aliases,
        "anchor_monday": "2025-12-29",
    }
    legend = _legend_with_aliases(ws, aliases)
    existing_codes = {str(row.values[0]).strip().upper() for row in legend if row.values}
    custom_codes = set(cycles)
    for pattern in cycles.values():
        custom_codes.update(token for token in pattern if token not in {"BASE", "TT", "D"})
    for code in sorted(custom_codes):
        if code not in existing_codes:
            legend.append(LegendRow([code, "Turno personalizado", "Definido en la plantilla", "Color automático por familia", ""]))
    return CalendarSpec(key, DISPLAY_NAMES[key], people, settings, legend)


def _calendar_farmacia(ws) -> CalendarSpec:
    aliases = _read_shift_aliases(ws)
    rows = _read_people_table_active(ws, ["Nombre", "Turno", "Teletrabajo"])
    people = [PersonSpec(name=str(x["Nombre"]).strip(), base_shift=str(x["Turno"] or "").strip().upper(), telework=_yes_no_tt(x["Teletrabajo"])) for x in rows]
    if len(people) != 2:
        raise TemplateValidationError("Farmacia debe tener exactamente dos personas para alternar los sábados.")
    settings = {
        "anchor_saturday": "2026-01-03",
        "first_saturday_person": str(_value_right(ws, "Comienza el 1er sábado del año") or "").strip(),
        "shift_aliases": aliases,
    }
    return CalendarSpec("Farmacia", DISPLAY_NAMES["Farmacia"], people, settings, _legend_with_aliases(ws, aliases))


def _calendar_sistemas(ws) -> CalendarSpec:
    aliases = _read_shift_aliases(ws)
    if _people_table_has_headers(ws, ["Grupo", "Nombre", "Turno base", "Patrón TT", "Teletrabajo", "Inicio ciclo TT"]):
        rows = _read_people_table_active(ws, ["Grupo", "Nombre", "Turno base", "Patrón TT", "Teletrabajo", "Inicio ciclo TT"])
        people = [
            PersonSpec(
                name=str(x["Nombre"]).strip(), group=str(x["Grupo"] or "").strip(),
                base_shift=str(x["Turno base"] or "M").strip().upper(),
                tt_pattern=str(x["Patrón TT"] or "").strip(), telework=_yes_no_tt(x["Teletrabajo"]),
                start_phase=_system_start_phase(x.get("Inicio ciclo TT")),
            )
            for x in rows
        ]
    else:
        rows = _read_people_table_active(ws, ["Grupo", "Nombre", "Turno base", "Patrón TT", "Teletrabajo"])
        people = [PersonSpec(name=str(x["Nombre"]).strip(), group=str(x["Grupo"] or "").strip(), base_shift=str(x["Turno base"] or "M").strip().upper(), tt_pattern=str(x["Patrón TT"] or "").strip(), telework=_yes_no_tt(x["Teletrabajo"])) for x in rows]
    return CalendarSpec("Sistemas", DISPLAY_NAMES["Sistemas"], people, {"tt_period": 3, "anchor_monday": "2025-12-29", "shift_aliases": aliases}, _legend_with_aliases(ws, aliases))


def _calendar_supervisores(ws) -> CalendarSpec:
    aliases = _read_shift_aliases(ws)
    if _people_table_has_headers(ws, ["Grupo", "Nombre", "Turno base", "Teletrabajo", "Orden TT"], after_label="SUPERVISORES"):
        rows = _read_people_table_active(ws, ["Grupo", "Nombre", "Turno base", "Teletrabajo", "Orden TT"], after_label="SUPERVISORES")
        people = [
            PersonSpec(
                name=str(x["Nombre"]).strip(), group=str(x["Grupo"] or "").strip(),
                base_shift=str(x["Turno base"] or "M").strip().upper(),
                telework=_yes_no_tt(x["Teletrabajo"]),
                start_phase=_phase_number(x.get("Orden TT"), "Supervisores · Orden TT", 12),
            )
            for x in rows
        ]
    else:
        rows = _read_people_table_active(ws, ["Grupo", "Nombre", "Turno base", "Teletrabajo"], after_label="SUPERVISORES")
        people = [PersonSpec(name=str(x["Nombre"]).strip(), group=str(x["Grupo"] or "").strip(), base_shift=str(x["Turno base"] or "M").strip().upper(), telework=_yes_no_tt(x["Teletrabajo"])) for x in rows]
    tt_pattern = _read_csv_pattern(_value_right(ws, "Ciclo TT (semanas)"), "Supervisores · Ciclo TT")
    if not any(token == "TT" for token in tt_pattern):
        raise TemplateValidationError("Supervisores: el Ciclo TT debe contener al menos una semana TT.")
    return CalendarSpec("Supervisores", DISPLAY_NAMES["Supervisores"], people, {"tt_period": len(tt_pattern), "tt_pattern": tt_pattern, "shift_aliases": aliases, "anchor_monday": "2025-12-29", "guard_anchor": "2025-12-29"}, _legend_with_aliases(ws, aliases), _read_guard_order(ws), _read_group_limits(ws))

def _validate_start_controls(spec: CalendarSpec) -> None:
    """Valida la coherencia de los selectores de inicio."""
    by_name = {p.name: p for p in spec.people}

    if spec.key == "Intensivo":
        name = str(spec.settings.get("start_tt_person", "") or "").strip()
        if name:
            person = by_name.get(name)
            if person is None:
                raise TemplateValidationError(
                    f"Intensivo: la persona elegida para iniciar la cinta no está activa: {name}."
                )
            if not person.telework_enabled:
                raise TemplateValidationError(
                    f"Intensivo: {name} tiene Teletrabajo=No y no puede ocupar la 1ª posición TT de la cinta."
                )

    elif spec.key == "Rotatorio":
        cycle = spec.settings.get("cycle", [])
        weeks = sum(int(days) for _, days in cycle) // 7 if cycle else 0
        for person in spec.people:
            if person.start_phase is not None and weeks and int(person.start_phase) > weeks:
                raise TemplateValidationError(
                    f"Rotatorio: {person.name} tiene fase {person.start_phase}, pero el ciclo actual solo tiene {weeks} semanas."
                )

    elif spec.key in {"EasyVista", "Puesto Usuario"}:
        period = int(spec.settings.get("tt_period", 0))
        for person in spec.people:
            if person.start_phase is None:
                continue
            if not person.telework_enabled:
                raise TemplateValidationError(
                    f"{spec.title}: {person.name} tiene Teletrabajo=No y no puede tener Inicio TT."
                )
            if period and int(person.start_phase) > period:
                raise TemplateValidationError(
                    f"{spec.title}: {person.name} tiene Inicio TT semana {person.start_phase}, "
                    f"pero el ciclo solo tiene {period} semanas."
                )

    elif spec.key == "Farmacia":
        name = str(spec.settings.get("first_saturday_person", "") or "").strip()
        if name and name not in by_name:
            raise TemplateValidationError(
                f"Farmacia: la persona elegida para el primer sábado no está activa: {name}."
            )

    elif spec.key == "Sistemas":
        for person in spec.people:
            if person.start_phase is None:
                continue
            if not person.telework_enabled:
                raise TemplateValidationError(
                    f"Sistemas: {person.name} tiene Teletrabajo=No y no puede configurar Inicio ciclo TT."
                )
            mode = _norm(person.tt_pattern)
            if "2" not in mode or "tt" not in mode or "siempre" in mode or mode.startswith("no "):
                raise TemplateValidationError(
                    f"Sistemas: {person.name} usa el patrón {person.tt_pattern!r}. "
                    "'Inicio ciclo TT' solo se aplica a '2 presenciales + 1 TT'."
                )

    elif spec.key == "Supervisores":
        period = int(spec.settings.get("tt_period", 0))
        for person in spec.people:
            if person.start_phase is None:
                continue
            if not person.telework_enabled:
                raise TemplateValidationError(
                    f"Supervisores: {person.name} tiene Teletrabajo=No y no puede tener Orden TT."
                )
            if period and int(person.start_phase) > period:
                raise TemplateValidationError(
                    f"Supervisores · {person.group}: {person.name} tiene TT semana {person.start_phase}, "
                    f"pero el ciclo es de {period} semanas."
                )


def _ensure_unique_names(spec: CalendarSpec) -> None:
    names = [p.name.casefold() for p in spec.people]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise TemplateValidationError(f"{spec.title}: hay nombres duplicados: {', '.join(dupes)}")
    if not spec.people:
        raise TemplateValidationError(f"{spec.title}: no hay personas configuradas.")


def load_template(path: str | Path) -> TemplateModel:
    path = Path(path)
    if not path.exists():
        raise TemplateValidationError(f"No existe la plantilla: {path}")
    if path.suffix.lower() != ".xlsx":
        raise TemplateValidationError("La plantilla debe ser un fichero .xlsx")

    try:
        wb = load_workbook(path, data_only=False, read_only=False)
    except Exception as exc:
        raise TemplateValidationError(f"No se ha podido abrir la plantilla: {exc}") from exc

    missing = [s for s in REQUIRED_SHEETS if s not in wb.sheetnames]
    if missing:
        raise TemplateValidationError(
            "La plantilla no es válida. Faltan las pestañas obligatorias: " + ", ".join(missing)
        )

    parsers = {
        "Intensivo": _calendar_intensivo,
        "Rotatorio": _calendar_rotatorio,
        "EasyVista": lambda ws: _calendar_easy_or_puesto(ws, "EasyVista", "EASYVISTA"),
        "Farmacia": _calendar_farmacia,
        "Puesto Usuario": lambda ws: _calendar_easy_or_puesto(ws, "Puesto Usuario", "GPT"),
        "Sistemas": _calendar_sistemas,
        "Supervisores": _calendar_supervisores,
    }

    calendars = {}
    order = [s for s in wb.sheetnames if s in CALENDAR_KEYS]
    for key in order:
        spec = parsers[key](wb[key])
        _ensure_unique_names(spec)
        _validate_start_controls(spec)
        calendars[key] = spec

    return TemplateModel(path=path, sheet_order=order, calendars=calendars)
