from datetime import date
import pytest

from turnos.models import CalendarSpec, HolidayInfo, PersonSpec
from turnos.scheduler import (
    SchedulingError, build_schedule, calendar_dates, calendar_start,
    is_tt_code, is_tt_renounced, validate_schedule, visible_code,
)


def test_calendar_starts_monday_and_has_54_weeks():
    assert calendar_start(2027).weekday() == 0
    assert len(calendar_dates(2027)) == 54 * 7


def test_tt_helpers_count_renunciation_as_tt():
    assert is_tt_code("M_TT")
    assert is_tt_code("M_TTR")
    assert is_tt_renounced("M_TTR")
    assert visible_code("M_TTR") == "M"


def test_intensivo_rejects_mathematically_impossible_tt_capacity():
    people = [PersonSpec(f"P{i:02d}", telework="Sí") for i in range(18)]
    spec = CalendarSpec("Intensivo", "Intensivo", people, {
        "period_weeks": 9, "max_p": 2, "max_tt": 4, "anchor_monday": "2025-12-29"
    })
    with pytest.raises(SchedulingError, match="no caben"):
        build_schedule(spec, 2027, {})


def test_intensivo_respects_p_and_tt_caps_when_feasible():
    people = [PersonSpec(f"P{i:02d}", telework="Sí" if i < 13 else "No", reduced=(i in {12, 13})) for i in range(18)]
    spec = CalendarSpec("Intensivo", "Intensivo", people, {
        "period_weeks": 9, "max_p": 2, "max_tt": 4, "anchor_monday": "2025-12-29"
    })
    schedule = build_schedule(spec, 2027, {})
    validate_schedule(spec, schedule, 2027)
    # Reducidos nunca P y trabajan como M1 fuera de descanso.
    for name in ("P12", "P13"):
        assert not any(visible_code(v) == "P" for v in schedule[name].values())
        assert any(visible_code(v) == "M1" for v in schedule[name].values())


def test_easyvista_one_tt_per_week():
    people = [
        PersonSpec("A", base_shift="M", telework="Sí"),
        PersonSpec("B", base_shift="MA", telework="Sí"),
        PersonSpec("C", base_shift="M", telework="Renuncia"),
    ]
    spec = CalendarSpec("EasyVista", "EasyVista", people, {"max_tt": 1, "tt_period": 3, "anchor_monday": "2025-12-29"})
    schedule = build_schedule(spec, 2027, {})
    dates = calendar_dates(2027)
    for i in range(0, len(dates), 7):
        week = dates[i:i+7]
        active = {p.name for p in people if any(is_tt_code(schedule[p.name][d]) for d in week)}
        assert len(active) <= 1


def test_farmacia_saturdays_alternate():
    spec = CalendarSpec("Farmacia", "Farmacia", [
        PersonSpec("F1 person", base_shift="F1", telework="No"),
        PersonSpec("F2 person", base_shift="F2", telework="No"),
    ], {"anchor_saturday": "2026-01-03"})
    schedule = build_schedule(spec, 2026, {})
    assert schedule["F1 person"][date(2026,1,3)] == "F1"
    assert schedule["F2 person"][date(2026,1,3)] == "D"
    assert schedule["F1 person"][date(2026,1,10)] == "D"
    assert schedule["F2 person"][date(2026,1,10)] == "F2"


def test_sistemas_ma_cyclic_do_not_coincide():
    people = [
        PersonSpec("MA1", group="G1", base_shift="MA", tt_pattern="2 presenciales + 1 TT", telework="Sí"),
        PersonSpec("MA2", group="G2", base_shift="MA", tt_pattern="2 presenciales + 1 TT", telework="Sí"),
        PersonSpec("M1", group="G1", base_shift="M", tt_pattern="Siempre TT", telework="Sí"),
    ]
    spec = CalendarSpec("Sistemas", "Sistemas", people, {"tt_period": 3, "anchor_monday":"2025-12-29"})
    schedule = build_schedule(spec, 2027, {})
    dates = calendar_dates(2027)
    for i in range(0, len(dates), 7):
        week = dates[i:i+7]
        ma_tt = sum(any(is_tt_code(schedule[n][d]) for d in week) for n in ("MA1","MA2"))
        assert ma_tt <= 1


def test_supervisores_guard_and_group_tt_limit():
    people = [
        PersonSpec("Daniel", group="Soporte N1", base_shift="M", telework="Sí"),
        PersonSpec("Marian", group="HCE", base_shift="M", telework="Sí"),
        PersonSpec("Adrian", group="Soporte N1", base_shift="M", telework="Renuncia"),
        PersonSpec("Isabel", group="Soporte N1", base_shift="M", telework="No"),
    ]
    spec = CalendarSpec(
        "Supervisores", "Supervisores y OPX", people,
        {"tt_period":3, "anchor_monday":"2025-12-29", "guard_anchor":"2025-12-29"},
        guard_order=["Daniel","Marian","Adrian"],
        group_tt_limits={"Soporte N1":1, "HCE":1},
    )
    schedule = build_schedule(spec, 2026, {})
    # Daniel tiene G durante toda la primera semana del ancla.
    for d in [date(2025,12,29), date(2026,1,1), date(2026,1,4)]:
        assert schedule["Daniel"][d] == "G"
    dates = calendar_dates(2026)
    for i in range(0, len(dates), 7):
        week = dates[i:i+7]
        soporte = ["Daniel","Adrian","Isabel"]
        tt = {n for n in soporte if any(is_tt_code(schedule[n][d]) for d in week)}
        assert len(tt) <= 1


def test_national_and_regional_holidays_rest_non_rotating():
    people = [PersonSpec("A", base_shift="M", telework="No")]
    spec = CalendarSpec("EasyVista", "EasyVista", people, {"max_tt":1,"tt_period":3,"anchor_monday":"2025-12-29"})
    h = {date(2027,1,1): HolidayInfo("Año Nuevo","national",("national",))}
    schedule = build_schedule(spec, 2027, h)
    assert schedule["A"][date(2027,1,1)] == "D"


def test_rotatorio_festive_suffix_and_weekend_behavior():
    # 12 personas permiten máximo 2 R con el ciclo de 84 días.
    people = [PersonSpec(f"R{i:02d}", telework="Sí") for i in range(12)]
    cycle = [("N",7),("D",8),("M",7),("D",2),("M",7),("D",2),("R",5),("D",4),
             ("N",7),("D",8),("T",7),("D",2),("T",7),("D",2),("R",5),("D",4)]
    spec = CalendarSpec("Rotatorio","Rotatorio",people,{"max_r":2,"cycle":cycle,"anchor_night":"2025-12-31"})
    holidays = {date(2026,1,1): HolidayInfo("Año Nuevo","national",("national",))}
    schedule = build_schedule(spec, 2026, holidays)
    validate_schedule(spec, schedule, 2026)
    # Nadie descansa automáticamente por el festivo: los turnos de trabajo usan sufijo F.
    codes = {visible_code(schedule[p.name][date(2026,1,1)]) for p in people}
    assert any(code in {"NF","MF","TF","RF"} for code in codes)
