from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Dict, Iterable, List, Sequence, Tuple

from .models import CalendarSpec, HolidayInfo, PersonSpec, Schedule

SEMANAS_VISIBLES = 54
DIAS_POR_SEMANA = 7


class SchedulingError(ValueError):
    pass


def calendar_start(year: int) -> date:
    jan1 = date(year, 1, 1)
    return jan1 - timedelta(days=jan1.weekday())


def calendar_dates(year: int) -> List[date]:
    start = calendar_start(year)
    return [start + timedelta(days=i) for i in range(SEMANAS_VISIBLES * DIAS_POR_SEMANA)]


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _week_index(d: date, anchor: date) -> int:
    return (_monday(d) - anchor).days // 7


def _rest_for_holiday(info: HolidayInfo | None) -> bool:
    """Indica si un festivo implica descanso en calendarios no rotatorios.

    Nacionales, autonómicos, locales y los opcionales de empresa (24/12,
    31/12) se tratan de la misma forma: D.
    """
    return bool(
        info
        and (
            info.has_scope("national")
            or info.has_scope("regional")
            or info.has_scope("local")
            or info.has_scope("custom")
        )
    )


def _tt_code(base: str, person: PersonSpec) -> str:
    if person.telework == "Renuncia":
        return f"{base}_TTR"
    if person.telework == "Sí":
        return f"{base}_TT"
    return base


def is_tt_code(code: str) -> bool:
    return str(code).endswith("_TT") or str(code).endswith("_TTR")


def is_tt_renounced(code: str) -> bool:
    return str(code).endswith("_TTR")


def visible_code(code: str) -> str:
    text = str(code)
    if text.endswith("_TTR"):
        return text[:-4]
    if text.endswith("_TT"):
        return text[:-3]
    return text




def _shift_aliases(spec: CalendarSpec) -> Dict[str, str]:
    return {str(k).upper(): str(v).upper() for k, v in dict(spec.settings.get("shift_aliases", {})).items()}


def shift_family(spec: CalendarSpec, code: str) -> str:
    """Resuelve un turno creado a su comportamiento base.

    Ej.: M2 -> M1. Se conserva M1 como familia especial para que Intensivo
    sepa que no participa en P.
    """
    aliases = _shift_aliases(spec)
    cur = str(code or "").upper()
    seen = set()
    while cur in aliases and cur not in seen:
        seen.add(cur)
        cur = aliases[cur]
    return cur


def _is_reduced_shift(spec: CalendarSpec, code: str) -> bool:
    return shift_family(spec, code) == "M1"


def _cycle_pattern_for_base(spec: CalendarSpec, patterns: Dict[str, Sequence[str]], base: str) -> Sequence[str] | None:
    cur = str(base).upper()
    seen = set()
    aliases = _shift_aliases(spec)
    while cur not in patterns and cur in aliases and cur not in seen:
        seen.add(cur)
        cur = aliases[cur]
    return patterns.get(cur)


def _tt_vector(phase: int, parity: int, enabled: bool, period: int = 9) -> set[int]:
    """Semanas TT sobre un superciclo de 18 semanas.

    Cada persona alterna:
      A = P-2, P-1, P+1
      B = P-1, P+1
    y vuelve a A. ``parity`` decide si la primera P del superciclo usa A o B.
    """
    if not enabled:
        return set()
    superperiod = period * 2
    out: set[int] = set()
    for occurrence in (phase, phase + period):
        occurrence_number = 0 if occurrence == phase else 1
        is_a = ((occurrence_number + parity) % 2) == 0
        offsets = (-2, -1, 1) if is_a else (-1, 1)
        for delta in offsets:
            out.add((occurrence + delta) % superperiod)
    return out


def _assign_intensivo_phases(spec: CalendarSpec) -> Dict[str, tuple[int, int]]:
    period = int(spec.settings.get("period_weeks", 9))
    max_p = int(spec.settings.get("max_p", 2))
    max_tt = int(spec.settings.get("max_tt", 4))
    if period <= 0 or max_p <= 0 or max_tt <= 0:
        raise SchedulingError("Intensivo: Semanas entre P, máximo P y máximo TT deben ser mayores que cero.")

    eligible_p = [p for p in spec.people if not (p.reduced or _is_reduced_shift(spec, p.base_shift))]
    if len(eligible_p) > period * max_p:
        raise SchedulingError(
            f"Intensivo: {len(eligible_p)} personas pueden hacer P, pero {period} semanas × {max_p} P "
            f"solo ofrecen {period * max_p} plazas."
        )

    active_tt = [p for p in spec.people if p.telework_enabled]
    # En dos ciclos de P cada persona activa usa 5 semanas TT.
    required = len(active_tt) * 5
    capacity = (period * 2) * max_tt
    if required > capacity:
        raise SchedulingError(
            "Intensivo: las reglas de Teletrabajo no caben con la plantilla actual. "
            f"{len(active_tt)} personas con TT generan {required} plazas TT cada {period * 2} semanas, "
            f"pero el máximo {max_tt} permite {capacity}. Marca alguna persona como 'No' en Teletrabajo "
            "o revisa el máximo TT."
        )

    p_counts = [0] * period
    tt_counts = [0] * (period * 2)
    assignments: Dict[str, tuple[int, int]] = {}

    # Primero las personas con más restricciones: hacen P y TT.
    indexed = list(enumerate(spec.people))
    indexed.sort(key=lambda t: (not t[1].telework_enabled, t[1].reduced, t[0]))

    for original_index, person in indexed:
        best = None
        for phase in range(period):
            if not (person.reduced or _is_reduced_shift(spec, person.base_shift)) and p_counts[phase] >= max_p:
                continue
            for parity in (0, 1):
                vec = _tt_vector(phase, parity, person.telework_enabled, period)
                if any(tt_counts[w] >= max_tt for w in vec):
                    continue
                new_tt = [tt_counts[i] + (1 if i in vec else 0) for i in range(period * 2)]
                new_p = p_counts.copy()
                if not (person.reduced or _is_reduced_shift(spec, person.base_shift)):
                    new_p[phase] += 1
                # Balancea TT primero, luego P; finalmente respeta orden/fase baja.
                score = (
                    max(new_tt), sum(x * x for x in new_tt),
                    max(new_p), sum(x * x for x in new_p),
                    new_p[phase], phase, parity,
                )
                if best is None or score < best[0]:
                    best = (score, phase, parity, vec)
        if best is None:
            raise SchedulingError(
                f"Intensivo: no se puede asignar una fase válida a {person.name} sin superar "
                f"máximo {max_p} P o {max_tt} TT por semana."
            )
        _, phase, parity, vec = best
        assignments[person.name] = (phase, parity)
        if not (person.reduced or _is_reduced_shift(spec, person.base_shift)):
            p_counts[phase] += 1
        for w in vec:
            tt_counts[w] += 1

    return assignments


def _normalize_intensivo_tape(raw: object) -> List[str]:
    if isinstance(raw, str):
        parts = [x.strip().upper() for x in raw.replace(";", ",").split(",") if x.strip()]
    else:
        parts = [str(x).strip().upper() for x in (raw or []) if str(x).strip()]
    return ["TT" if x in {"T", "TT"} else x for x in parts]


def _validate_intensivo_tape(spec: CalendarSpec, tape: List[str]) -> None:
    if not tape:
        raise SchedulingError("Intensivo: la cinta de rotación está vacía.")
    invalid = [x for x in tape if x not in {"M", "P", "TT"}]
    if invalid:
        raise SchedulingError("Intensivo: la cinta solo admite M, P y TT.")
    if len(tape) != len(spec.people):
        raise SchedulingError(
            f"Intensivo: la cinta tiene {len(tape)} posiciones y hay {len(spec.people)} personas activas. "
            "Para conservar el desplazamiento por orden de filas, ambos números deben coincidir."
        )
    max_p = int(spec.settings.get("max_p", 2))
    max_tt = int(spec.settings.get("max_tt", 5))
    period = int(spec.settings.get("period_weeks", 9))
    p_positions = [i for i, state in enumerate(tape) if state == "P"]
    if len(p_positions) == 2:
        gaps = sorted(((p_positions[1] - p_positions[0]) % len(tape), (p_positions[0] - p_positions[1]) % len(tape)))
        if gaps != [period, period]:
            raise SchedulingError(
                f"Intensivo: 'Semanas entre P' vale {period}, pero las P de la cinta no están separadas "
                f"{period} semanas. Ajusta la cinta o ese valor."
            )
    if tape.count("P") > max_p:
        raise SchedulingError(
            f"Intensivo: la cinta contiene {tape.count('P')} posiciones P y el máximo configurado es {max_p}."
        )
    if tape.count("TT") > max_tt:
        raise SchedulingError(
            f"Intensivo: la cinta contiene {tape.count('TT')} posiciones TT y el máximo configurado es {max_tt}."
        )


def _schedule_intensivo_tape(spec: CalendarSpec, year: int, holidays: Dict[date, HolidayInfo]) -> Schedule:
    tape = _normalize_intensivo_tape(spec.settings.get("tape"))
    _validate_intensivo_tape(spec, tape)
    start_person = str(spec.settings.get("start_tt_person", "") or "").strip()
    if start_person:
        if start_person not in spec.names:
            raise SchedulingError(
                f"Intensivo: la persona elegida para iniciar la cinta ({start_person}) no está activa en la plantilla."
            )
        selected = next(p for p in spec.people if p.name == start_person)
        if not selected.telework_enabled:
            raise SchedulingError(
                f"Intensivo: {start_person} tiene Teletrabajo=No y no puede ocupar la 1ª posición TT de la cinta."
            )
        anchor = calendar_start(year)
        start_index = spec.names.index(start_person)
        reset_each_year = True
    else:
        anchor = date.fromisoformat(str(spec.settings.get("anchor_tape_monday", "2026-12-14")))
        if anchor.weekday() != 0:
            raise SchedulingError("Intensivo: la fecha ancla de la cinta debe ser lunes.")
        start_index = 0
        reset_each_year = False

    dates = calendar_dates(year)
    schedule: Schedule = {}
    width = len(tape)

    for person_index, person in enumerate(spec.people):
        base = person.base_shift or ("M1" if person.reduced else "M")
        if person.reduced and not _is_reduced_shift(spec, base):
            base = "M1"
        planned: Dict[date, str] = {}
        for d in dates:
            if d.weekday() >= 5:
                code = "D"
            elif _rest_for_holiday(holidays.get(d)):
                code = "D"
            else:
                week_shift = _week_index(d, anchor)
                # Si la plantilla elige una persona inicial, esa persona ocupa
                # la primera TT de la cinta en la primera semana visible del cuadrante. Después la
                # cinta baja una fila por semana. Sin selección se conserva la
                # ancla histórica de versiones anteriores.
                state = tape[(person_index - start_index - week_shift) % width]
                if state == "P" and not _is_reduced_shift(spec, base):
                    code = "P"
                elif state == "TT":
                    code = _tt_code(base, person)
                else:
                    code = base
            planned[d] = code
        schedule[person.name] = planned
    return schedule


def schedule_intensivo(spec: CalendarSpec, year: int, holidays: Dict[date, HolidayInfo]) -> Schedule:
    # v2.5: la plantilla mantiene la cinta circular real del Intensivo.
    # Si no existe (plantillas antiguas), se conserva el algoritmo A/B previo.
    if spec.settings.get("tape"):
        return _schedule_intensivo_tape(spec, year, holidays)

    period = int(spec.settings.get("period_weeks", 9))
    anchor = date.fromisoformat(str(spec.settings.get("anchor_monday", "2025-12-29")))
    if anchor.weekday() != 0:
        raise SchedulingError("Intensivo: la fecha ancla debe ser lunes.")
    assignments = _assign_intensivo_phases(spec)
    dates = calendar_dates(year)
    schedule: Schedule = {}

    for person in spec.people:
        phase, parity = assignments[person.name]
        planned: Dict[date, str] = {}
        for d in dates:
            wi = _week_index(d, anchor)
            cycle_phase = wi % period
            superphase = wi % (period * 2)
            occurrence_index = (wi - phase) // period
            is_p_week = cycle_phase == phase
            if d.weekday() >= 5:
                code = "D"
            elif _rest_for_holiday(holidays.get(d)):
                code = "D"
            elif is_p_week and not (person.reduced or _is_reduced_shift(spec, person.base_shift)):
                code = "P"
            else:
                base = person.base_shift or ("M1" if person.reduced else "M")
                if person.reduced and not _is_reduced_shift(spec, base):
                    base = "M1"
                tt_weeks = _tt_vector(phase, parity, person.telework_enabled, period)
                code = _tt_code(base, person) if superphase in tt_weeks else base
            planned[d] = code
        schedule[person.name] = planned
    return schedule


def _expand_cycle(parts: Sequence[tuple[str, int]]) -> List[str]:
    out: List[str] = []
    for code, count in parts:
        count = int(count)
        if count <= 0:
            raise SchedulingError(f"Duración inválida para {code}: {count}")
        out.extend([str(code).upper()] * count)
    if not out:
        raise SchedulingError("El ciclo no puede estar vacío.")
    return out


def _max_counts_for_offsets(cycle: List[str], offsets: Sequence[int], code: str) -> int:
    peak = 0
    for day in range(len(cycle)):
        peak = max(peak, sum(1 for off in offsets if cycle[(day + off) % len(cycle)] == code))
    return peak


def choose_offsets(operator_count: int, cycle: List[str], code: str, maximum: int, phase_step: int = 7) -> List[int]:
    candidates = list(range(0, len(cycle), phase_step))
    offsets: List[int] = []
    usage: Counter[int] = Counter()
    for _ in range(operator_count):
        options = []
        for off in candidates:
            peak = _max_counts_for_offsets(cycle, offsets + [off], code)
            if peak <= maximum:
                options.append(((peak, usage[off], off), off))
        if not options:
            raise SchedulingError(
                f"Rotatorio: no existe una distribución para {operator_count} personas con máximo {maximum} {code}."
            )
        _, chosen = min(options)
        offsets.append(chosen)
        usage[chosen] += 1
    return offsets

def choose_offsets_with_fixed(people: Sequence[PersonSpec], cycle: List[str], code: str, maximum: int, phase_step: int = 7) -> List[int]:
    """Combina fases iniciales elegidas por usuario con asignación automática."""
    candidates = list(range(0, len(cycle), phase_step))
    offsets: List[int | None] = [None] * len(people)
    used: List[int] = []
    usage: Counter[int] = Counter()

    for i, person in enumerate(people):
        if person.start_phase is None:
            continue
        off = (int(person.start_phase) - 1) * phase_step
        if off not in candidates:
            raise SchedulingError(f"Rotatorio: fase inicial no válida para {person.name}: {person.start_phase}.")
        if _max_counts_for_offsets(cycle, used + [off], code) > maximum:
            raise SchedulingError(
                f"Rotatorio: las fases iniciales elegidas superan el máximo {maximum} {code}. "
                f"Revisa la fase de {person.name}."
            )
        offsets[i] = off
        used.append(off)
        usage[off] += 1

    for i, person in enumerate(people):
        if offsets[i] is not None:
            continue
        options = []
        for off in candidates:
            peak = _max_counts_for_offsets(cycle, used + [off], code)
            if peak <= maximum:
                options.append(((peak, usage[off], off), off))
        if not options:
            raise SchedulingError(
                f"Rotatorio: no se puede completar la distribución de {person.name} con máximo {maximum} {code}."
            )
        _, chosen = min(options)
        offsets[i] = chosen
        used.append(chosen)
        usage[chosen] += 1
    return [int(x) for x in offsets]


def _decorate_rotatorio(d: date, base: str, family: str, holidays: Dict[date, HolidayInfo]) -> str:
    if family == "D":
        return "D"
    if _rest_for_holiday(holidays.get(d)):
        if base == family:
            return {"M": "MF", "T": "TF", "N": "NF", "R": "RF"}.get(family, base)
        return f"{base}F" if family in {"M", "T", "N", "R", "M1"} else base
    if d.weekday() == 6:
        if base == family:
            return {"M": "MD", "T": "TD", "N": "ND"}.get(family, base)
        return f"{base}D" if family in {"M", "T", "N", "M1"} else base
    return base


def schedule_rotatorio(spec: CalendarSpec, year: int, holidays: Dict[date, HolidayInfo]) -> Schedule:
    cycle = _expand_cycle(spec.settings.get("cycle", []))
    if len(cycle) % 7:
        raise SchedulingError("Rotatorio: el ciclo completo debe durar semanas completas.")
    max_r = int(spec.settings.get("max_r", 2))
    cycle_families = [shift_family(spec, code) for code in cycle]
    explicit_start = any(p.start_phase is not None for p in spec.people)
    if explicit_start:
        offsets = choose_offsets_with_fixed(spec.people, cycle_families, "R", max_r, phase_step=7)
        anchor = calendar_start(year) + timedelta(days=2)  # miércoles de la primera semana visible
    else:
        offsets = choose_offsets(len(spec.people), cycle_families, "R", max_r, phase_step=7)
        anchor = date.fromisoformat(str(spec.settings.get("anchor_night", "2025-12-31")))
    dates = calendar_dates(year)
    if anchor.weekday() != 2:
        raise SchedulingError("Rotatorio: la fecha ancla de N debe ser miércoles.")

    # El ciclo de plantilla comienza por N. Todos los offsets son semanas completas.
    for off in offsets:
        if cycle[off % len(cycle)] != "N":
            # El operador no tiene por qué estar en N en el ancla; su propio inicio
            # de N seguirá cayendo en miércoles por ser off múltiplo de 7.
            pass

    schedule: Schedule = {}
    for person, off in zip(spec.people, offsets):
        row: Dict[date, str] = {}
        for d in dates:
            idx = ((d - anchor).days + off) % len(cycle)
            base = cycle[idx]
            family = shift_family(spec, base)
            decorated = _decorate_rotatorio(d, base, family, holidays)
            # M/M1 y R son TT únicamente L-V y cuando el día no es festivo.
            if family in {"M", "M1", "R"} and d.weekday() <= 4 and d not in holidays and person.telework_enabled:
                decorated = _tt_code(decorated, person)
            row[d] = decorated
        schedule[person.name] = row
    return schedule


def _assign_three_week_phases(people: List[PersonSpec], maximum: int, *, only_base: str | None = None) -> Dict[str, int]:
    phases = [0, 0, 0]
    out: Dict[str, int] = {}
    for person in people:
        if not person.telework_enabled:
            continue
        if only_base and person.base_shift != only_base:
            continue
        choices = [(phases[p], p) for p in range(3) if phases[p] < maximum]
        if not choices:
            raise SchedulingError("No hay capacidad suficiente en el ciclo TT de 3 semanas.")
        _, chosen = min(choices)
        out[person.name] = chosen
        phases[chosen] += 1
    return out


def _weekly_pattern_tt_weeks(pattern: Sequence[str], offset: int) -> set[int]:
    period = len(pattern)
    return {w for w in range(period) if str(pattern[(w + offset) % period]).upper() == "TT"}

def _offset_for_desired_tt_week(pattern: Sequence[str], desired_week: int) -> int:
    """Devuelve el desfase que hace que haya TT en la semana 1..N indicada."""
    period = len(pattern)
    if not 1 <= int(desired_week) <= period:
        raise SchedulingError(f"La semana TT debe estar entre 1 y {period}.")
    target = int(desired_week) - 1
    candidates = [off for off in range(period) if str(pattern[(target + off) % period]).upper() == "TT"]
    if not candidates:
        raise SchedulingError("El ciclo seleccionado no contiene ninguna semana TT.")
    return min(candidates)


def _assign_weekly_cycle_offsets(
    spec: CalendarSpec,
    patterns: Dict[str, Sequence[str]],
    maximum: int,
) -> Dict[str, int]:
    """Asigna desfases a ciclos semanales editables respetando el máximo TT.

    El patrón se define por turno base en la plantilla. Por ejemplo:
    ``M,M,TT`` o ``TT,TT,TT``. Los desfases permiten que varias personas
    con el mismo patrón no coincidan necesariamente en su semana TT.
    """
    period = int(spec.settings.get("tt_period", 0))
    if period <= 0:
        raise SchedulingError(f"{spec.title}: el ciclo semanal debe tener al menos una semana.")
    if maximum <= 0:
        raise SchedulingError(f"{spec.title}: Máximo TT por semana debe ser mayor que cero.")

    for base, pattern in patterns.items():
        if len(pattern) != period:
            raise SchedulingError(f"{spec.title}: el turno {base} no tiene {period} semanas de ciclo.")

    indexed = list(enumerate(spec.people))
    indexed.sort(
        key=lambda x: (
            -sum(1 for t in (_cycle_pattern_for_base(spec, patterns, x[1].base_shift) or []) if str(t).upper() == "TT")
            if x[1].telework_enabled else 0,
            x[0],
        )
    )
    counts = [0] * period
    out: Dict[str, int] = {}

    def rec(pos: int) -> bool:
        if pos >= len(indexed):
            return True
        _, person = indexed[pos]
        pattern = _cycle_pattern_for_base(spec, patterns, person.base_shift)
        if pattern is None:
            raise SchedulingError(
                f"{spec.title}: no existe ciclo semanal para el turno base {person.base_shift!r} de {person.name}."
            )

        options = []
        if person.start_phase is not None and not person.telework_enabled:
            raise SchedulingError(
                f"{spec.title}: {person.name} tiene Teletrabajo=No y no puede tener Inicio TT."
            )
        if person.start_phase is not None and person.telework_enabled:
            if int(person.start_phase) > period:
                raise SchedulingError(
                    f"{spec.title}: {person.name} tiene Inicio TT semana {person.start_phase}, "
                    f"pero el ciclo solo tiene {period} semanas."
                )
            offsets_to_try = [_offset_for_desired_tt_week(pattern, int(person.start_phase))]
        else:
            offsets_to_try = list(range(period))
        for off in offsets_to_try:
            tt_weeks = _weekly_pattern_tt_weeks(pattern, off) if person.telework_enabled else set()
            if any(counts[w] + 1 > maximum for w in tt_weeks):
                continue
            new_counts = [counts[w] + (1 if w in tt_weeks else 0) for w in range(period)]
            score = (max(new_counts), sum(v * v for v in new_counts), off)
            options.append((score, off, tt_weeks))
        for _, off, tt_weeks in sorted(options):
            out[person.name] = off
            for w in tt_weeks:
                counts[w] += 1
            if rec(pos + 1):
                return True
            for w in tt_weeks:
                counts[w] -= 1
            out.pop(person.name, None)
        return False

    if not rec(0):
        raise SchedulingError(
            f"{spec.title}: el ciclo editable no cabe con máximo {maximum} TT por semana. "
            "Si has cambiado un ciclo a TT,TT,TT, aumenta 'Máximo TT por semana' o reduce las personas "
            "con Teletrabajo=Sí/Renuncia."
        )
    return out


def _weekly_cycle_token(pattern: Sequence[str], week_index: int, offset: int) -> str:
    return str(pattern[(week_index + offset) % len(pattern)]).upper()


def schedule_easy_puesto(spec: CalendarSpec, year: int, holidays: Dict[date, HolidayInfo]) -> Schedule:
    max_tt = int(spec.settings.get("max_tt", 1))
    period = int(spec.settings.get("tt_period", 3))
    patterns = {str(k).upper(): list(v) for k, v in dict(spec.settings.get("weekly_cycles", {})).items()}
    if not patterns:
        # Compatibilidad con plantillas anteriores.
        patterns = {p.base_shift: ["BASE", "BASE", "TT"] for p in spec.people}
        period = 3
    offsets = _assign_weekly_cycle_offsets(spec, patterns, max_tt)
    if any(p.start_phase is not None for p in spec.people):
        anchor = calendar_start(year)
    else:
        anchor = date.fromisoformat(str(spec.settings.get("anchor_monday", "2025-12-29")))
    dates = calendar_dates(year)
    schedule: Schedule = {}
    for person in spec.people:
        row: Dict[date, str] = {}
        pattern = _cycle_pattern_for_base(spec, patterns, person.base_shift)
        if pattern is None:
            raise SchedulingError(f"{spec.title}: no existe ciclo para {person.base_shift}.")
        off = offsets[person.name]
        for d in dates:
            if d.weekday() >= 5 or _rest_for_holiday(holidays.get(d)):
                code = "D"
            else:
                base = person.base_shift or "M"
                token = _weekly_cycle_token(pattern, _week_index(d, anchor), off)
                if token == "TT":
                    code = _tt_code(base, person) if person.telework_enabled else base
                elif token in {"BASE", base}:
                    code = base
                else:
                    code = token
            row[d] = code
        schedule[person.name] = row
    return schedule


def schedule_farmacia(spec: CalendarSpec, year: int, holidays: Dict[date, HolidayInfo]) -> Schedule:
    if len(spec.people) != 2:
        raise SchedulingError("Farmacia necesita exactamente 2 personas.")
    families = {shift_family(spec, p.base_shift) for p in spec.people}
    if families != {"F1", "F2"}:
        raise SchedulingError("Farmacia necesita dos turnos que se comporten como F1 y F2.")
    first_person = str(spec.settings.get("first_saturday_person", "") or "").strip()
    if first_person:
        by_name = {p.name: p for p in spec.people}
        if first_person not in by_name:
            raise SchedulingError(f"Farmacia: la persona elegida para el primer sábado no está activa: {first_person}.")
        anchor = date(year, 1, 1)
        while anchor.weekday() != 5:
            anchor += timedelta(days=1)
        first_family = shift_family(spec, by_name[first_person].base_shift)
        if first_family not in {"F1", "F2"}:
            raise SchedulingError("Farmacia: la persona del primer sábado debe comportarse como F1 o F2.")
    else:
        anchor = date.fromisoformat(str(spec.settings.get("anchor_saturday", "2026-01-03")))
        first_family = "F1"
    if anchor.weekday() != 5:
        raise SchedulingError("Farmacia: la fecha ancla debe ser sábado.")
    dates = calendar_dates(year)
    schedule: Schedule = {p.name: {} for p in spec.people}
    for d in dates:
        holiday_rest = _rest_for_holiday(holidays.get(d))
        week_num = (d - anchor).days // 7
        other_family = "F2" if first_family == "F1" else "F1"
        saturday_family = first_family if week_num % 2 == 0 else other_family
        for p in spec.people:
            if holiday_rest:
                code = "D"
            elif d.weekday() <= 4:
                code = p.base_shift
            elif d.weekday() == 5:
                code = p.base_shift if shift_family(spec, p.base_shift) == saturday_family else "D"
            else:
                code = "D"
            schedule[p.name][d] = code
    return schedule


def schedule_sistemas(spec: CalendarSpec, year: int, holidays: Dict[date, HolidayInfo]) -> Schedule:
    explicit_start = any(p.start_phase is not None for p in spec.people)
    anchor = calendar_start(year) if explicit_start else date.fromisoformat(str(spec.settings.get("anchor_monday", "2025-12-29")))
    dates = calendar_dates(year)

    for p in spec.people:
        if p.start_phase is None:
            continue
        mode = _norm_pattern(p.tt_pattern)
        if not p.telework_enabled:
            raise SchedulingError(
                f"Sistemas: {p.name} tiene Teletrabajo=No y no puede configurar Inicio ciclo TT."
            )
        if "2" not in mode or "tt" not in mode or "siempre" in mode or mode.startswith("no "):
            raise SchedulingError(
                f"Sistemas: {p.name} usa el patrón {p.tt_pattern!r}. "
                "'Inicio ciclo TT' solo se aplica a '2 presenciales + 1 TT'."
            )

    cyclic = [p for p in spec.people if "2" in _norm_pattern(p.tt_pattern) and p.telework_enabled]
    explicit_offsets: Dict[str, int] = {}
    for p in cyclic:
        if p.start_phase is not None:
            if not 1 <= int(p.start_phase) <= 3:
                raise SchedulingError(f"Sistemas: Inicio ciclo TT no válido para {p.name}.")
            explicit_offsets[p.name] = int(p.start_phase) - 1

    # MA cíclicos no deben coincidir en su semana TT.
    ma_cyclic = [p for p in cyclic if shift_family(spec, p.base_shift) == "MA"]
    used_ma_tt: set[int] = set()
    auto_ma_offsets: Dict[str, int] = {}
    for p in ma_cyclic:
        if p.name in explicit_offsets:
            tt_week = (2 - explicit_offsets[p.name]) % 3
            if tt_week in used_ma_tt:
                raise SchedulingError(
                    f"Sistemas: los MA {p.name} y otro compañero coinciden en TT. Cambia 'Inicio ciclo TT'."
                )
            used_ma_tt.add(tt_week)
        else:
            choices = [off for off in range(3) if (2 - off) % 3 not in used_ma_tt]
            if not choices:
                raise SchedulingError("Sistemas: no hay fase libre para evitar coincidencia de MA en TT.")
            off = choices[0]
            auto_ma_offsets[p.name] = off
            used_ma_tt.add((2 - off) % 3)

    other_cyclic = [p for p in cyclic if p not in ma_cyclic]
    auto_other_offsets: Dict[str, int] = {}
    next_off = 0
    for p in other_cyclic:
        if p.name not in explicit_offsets:
            auto_other_offsets[p.name] = next_off % 3
            next_off += 1

    schedule: Schedule = {}
    for p in spec.people:
        row: Dict[date, str] = {}
        mode = _norm_pattern(p.tt_pattern)
        off = explicit_offsets.get(p.name, auto_ma_offsets.get(p.name, auto_other_offsets.get(p.name, 0)))
        for d in dates:
            if d.weekday() >= 5 or _rest_for_holiday(holidays.get(d)):
                code = "D"
            else:
                base = p.base_shift or "M"
                make_tt = False
                if p.telework_enabled:
                    if "siempre" in mode:
                        make_tt = True
                    elif "2" in mode:
                        make_tt = (_week_index(d, anchor) + off) % 3 == 2
                code = _tt_code(base, p) if make_tt else base
            row[d] = code
        schedule[p.name] = row
    return schedule


def _norm_pattern(text: str) -> str:
    return " ".join(str(text or "").strip().casefold().split())


def _assign_supervisor_tt_offsets(
    spec: CalendarSpec,
    group_people: Sequence[PersonSpec],
    pattern: Sequence[str],
    maximum: int,
    anchor: date,
    guard_anchor: date,
) -> Dict[str, int]:
    """Distribuye TT por grupo y respeta el orden inicial elegido en rosa."""
    invalid_start = [p for p in group_people if p.start_phase is not None and not p.telework_enabled]
    if invalid_start:
        person = invalid_start[0]
        raise SchedulingError(
            f"Supervisores: {person.name} tiene Teletrabajo=No y no puede tener Orden TT."
        )
    active = [p for p in group_people if p.telework_enabled]
    if not active:
        return {}
    period = len(pattern)
    # La guardia no exime del máximo de TT: cuenta como cualquier semana TT.
    horizon = period

    counts = [0] * horizon
    result: Dict[str, int] = {}

    # Primero se fijan las fases seleccionadas por usuario. start_phase indica
    # en qué semana (1..N) debe aparecer TT por primera vez.
    for p in active:
        if p.start_phase is None:
            continue
        if int(p.start_phase) > period:
            raise SchedulingError(
                f"Supervisores · {p.group}: {p.name} tiene TT semana {p.start_phase}, "
                f"pero el ciclo es de {period} semanas."
            )
        off = _offset_for_desired_tt_week(pattern, int(p.start_phase))
        actual_tt = [
            w for w in range(horizon)
            if _weekly_cycle_token(pattern, w, off) == "TT"
        ]
        if any(counts[w] + 1 > maximum for w in actual_tt):
            raise SchedulingError(
                f"Supervisores · {p.group}: el Orden TT elegido supera el máximo {maximum}. "
                f"Revisa a {p.name}."
            )
        result[p.name] = off
        for w in actual_tt:
            counts[w] += 1

    pending = [p for p in active if p.name not in result]
    best_solution = None
    best_score = None

    def rec(i: int):
        nonlocal best_solution, best_score
        if i == len(pending):
            score = (max(counts) if counts else 0, sum(x * x for x in counts), tuple(result.get(p.name, 0) for p in active))
            if best_score is None or score < best_score:
                best_score = score
                best_solution = dict(result)
            return
        p = pending[i]
        options = []
        for off in range(period):
            actual_tt = [w for w in range(horizon) if _weekly_cycle_token(pattern, w, off) == "TT"]
            if any(counts[w] + 1 > maximum for w in actual_tt):
                continue
            projected = [counts[w] + (1 if w in actual_tt else 0) for w in range(horizon)]
            options.append(((max(projected), sum(x*x for x in projected), off), off, actual_tt))
        for _, off, actual_tt in sorted(options):
            result[p.name] = off
            for w in actual_tt:
                counts[w] += 1
            rec(i + 1)
            for w in actual_tt:
                counts[w] -= 1
            result.pop(p.name, None)

    rec(0)
    if pending and best_solution is None:
        raise SchedulingError(
            f"Supervisores · {group_people[0].group if group_people else ''}: el ciclo TT no cabe con máximo {maximum}."
        )
    return best_solution if pending else dict(result)


def schedule_supervisores(spec: CalendarSpec, year: int, holidays: Dict[date, HolidayInfo]) -> Schedule:
    explicit_tt_start = any(p.start_phase is not None for p in spec.people)
    anchor = calendar_start(year) if explicit_tt_start else date.fromisoformat(str(spec.settings.get("anchor_monday", "2025-12-29")))
    guard_anchor = date.fromisoformat(str(spec.settings.get("guard_anchor", "2025-12-29")))
    pattern = [str(x).upper() for x in spec.settings.get("tt_pattern", ["BASE", "BASE", "TT"])]
    if not pattern:
        raise SchedulingError("Supervisores: el ciclo TT está vacío.")
    names = {p.name for p in spec.people}
    unknown = [n for n in spec.guard_order if n not in names]
    if unknown:
        raise SchedulingError("Supervisores: personas de Guardia no encontradas: " + ", ".join(unknown))

    groups: Dict[str, List[PersonSpec]] = defaultdict(list)
    for p in spec.people:
        groups[p.group].append(p)

    offset_by_name: Dict[str, int] = {}
    for group, people in groups.items():
        active = [p for p in people if p.telework_enabled]
        maximum = spec.group_tt_limits.get(group, max(1, len(active)))
        offset_by_name.update(
            _assign_supervisor_tt_offsets(spec, people, pattern, maximum, anchor, guard_anchor)
        )

    dates = calendar_dates(year)
    schedule: Schedule = {p.name: {} for p in spec.people}
    for d in dates:
        guard_name = None
        if spec.guard_order:
            gw = _week_index(d, guard_anchor) % len(spec.guard_order)
            guard_name = spec.guard_order[gw]
        wi = _week_index(d, anchor)
        for p in spec.people:
            base = p.base_shift or "M"
            off = offset_by_name.get(p.name, 0)
            token = _weekly_cycle_token(pattern, wi, off) if p.telework_enabled else "BASE"
            # La guardia trabaja también en festivos y conserva su ciclo TT.
            if p.name == guard_name:
                code = _tt_code("G", p) if token == "TT" else "G"
            elif _rest_for_holiday(holidays.get(d)) or d.weekday() >= 5:
                code = "D"
            else:
                if token == "TT":
                    code = _tt_code(base, p)
                elif token in {"BASE", base}:
                    code = base
                else:
                    code = token
            schedule[p.name][d] = code
    return schedule


def build_schedule(spec: CalendarSpec, year: int, holidays: Dict[date, HolidayInfo]) -> Schedule:
    if spec.key == "Intensivo":
        return schedule_intensivo(spec, year, holidays)
    if spec.key == "Rotatorio":
        return schedule_rotatorio(spec, year, holidays)
    if spec.key in {"EasyVista", "Puesto Usuario"}:
        return schedule_easy_puesto(spec, year, holidays)
    if spec.key == "Farmacia":
        return schedule_farmacia(spec, year, holidays)
    if spec.key == "Sistemas":
        return schedule_sistemas(spec, year, holidays)
    if spec.key == "Supervisores":
        return schedule_supervisores(spec, year, holidays)
    raise SchedulingError(f"Calendario no soportado: {spec.key}")


def validate_schedule(spec: CalendarSpec, schedule: Schedule, year: int) -> None:
    dates = calendar_dates(year)
    if set(schedule) != set(spec.names):
        raise SchedulingError(f"{spec.title}: el calendario generado no contiene exactamente las personas de la plantilla.")

    if spec.key == "Intensivo":
        max_p = int(spec.settings.get("max_p", 2))
        max_tt = int(spec.settings.get("max_tt", 4))
        for monday_idx in range(0, len(dates), 7):
            week = dates[monday_idx:monday_idx + 7]
            p_people = {
                name for name in spec.names
                if any(visible_code(schedule[name][d]) == "P" for d in week)
            }
            tt_people = {
                name for name in spec.names
                if any(is_tt_code(schedule[name][d]) for d in week)
            }
            if len(p_people) > max_p:
                raise SchedulingError(f"Intensivo: semana {week[0]} supera {max_p} P ({len(p_people)}).")
            if len(tt_people) > max_tt:
                raise SchedulingError(f"Intensivo: semana {week[0]} supera {max_tt} TT ({len(tt_people)}).")

    if spec.key == "Rotatorio":
        max_r = int(spec.settings.get("max_r", 2))
        for d in dates:
            r = sum(shift_family(spec, visible_code(schedule[n][d]).removesuffix("F").removesuffix("D")) == "R" for n in spec.names)
            if r > max_r:
                raise SchedulingError(f"Rotatorio: {d} tiene {r} R/RF; máximo {max_r}.")
