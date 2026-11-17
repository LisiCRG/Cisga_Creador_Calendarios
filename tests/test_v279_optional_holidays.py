from datetime import date

import turnos.holidays_provider as hp
from turnos.holidays_provider import _add_configurable_december_holiday
from turnos.models import CalendarSpec, HolidayInfo, PersonSpec
from turnos.scheduler import build_schedule, visible_code


def test_optional_holiday_can_be_added_without_overwriting_existing_name():
    holidays = {date(2027, 12, 24): HolidayInfo("Festivo previo", "local", ("local",))}
    _add_configurable_december_holiday(holidays, date(2027, 12, 24), "24 de diciembre")
    info = holidays[date(2027, 12, 24)]
    assert info.name == "Festivo previo"
    assert info.has_scope("local")
    assert info.has_scope("custom")


def test_custom_holiday_rests_non_rotating_calendar():
    d = date(2027, 12, 24)
    spec = CalendarSpec(
        "EasyVista", "EasyVista",
        [PersonSpec("A", base_shift="M", telework="No")],
        {"max_tt": 1, "tt_period": 3, "anchor_monday": "2025-12-29"},
    )
    holidays = {d: HolidayInfo("24 de diciembre", "custom", ("custom",))}
    schedule = build_schedule(spec, 2027, holidays)
    assert schedule["A"][d] == "D"


def test_custom_holiday_decorates_rotatorio_as_festive():
    d = date(2027, 12, 31)
    people = [PersonSpec(f"R{i:02d}", telework="Sí") for i in range(12)]
    cycle = [("N",7),("D",8),("M",7),("D",2),("M",7),("D",2),("R",5),("D",4),
             ("N",7),("D",8),("T",7),("D",2),("T",7),("D",2),("R",5),("D",4)]
    spec = CalendarSpec("Rotatorio", "Rotatorio", people, {"max_r": 2, "cycle": cycle, "anchor_night": "2025-12-31"})
    holidays = {d: HolidayInfo("31 de diciembre", "custom", ("custom",))}
    schedule = build_schedule(spec, 2027, holidays)
    codes = {visible_code(schedule[p.name][d]) for p in people}
    assert any(code in {"NF", "MF", "TF", "RF"} for code in codes)


def test_build_calendar_applies_checked_date_to_visible_adjacent_years(monkeypatch):
    class FakeHolidays:
        @staticmethod
        def Spain(**kwargs):
            return {}

    monkeypatch.setattr(hp, "_load_holidays_lib", lambda: FakeHolidays)
    holidays = hp.build_holiday_calendar(
        2027,
        "Castilla y León",
        "Valladolid",
        include_adjacent_years=True,
        require_local_for_target_year=False,
        dec24_holiday=True,
        dec31_holiday=False,
    )
    for year in (2026, 2027, 2028):
        assert holidays[date(year, 12, 24)].has_scope("custom")
        assert date(year, 12, 31) not in holidays


def test_optional_december_holiday_header_is_ochre_in_generated_excel(tmp_path):
    from pathlib import Path
    from openpyxl import load_workbook
    from turnos.excel_generator import default_output_filename, generate_excel
    from turnos.scheduler import calendar_dates
    from turnos.template_reader import load_template

    root = Path(__file__).resolve().parents[1]
    template = root / "templates" / "Plantilla_Cuadrantes_Usuarios_v13.xlsx"
    model = load_template(template)
    spec = model.calendars["EasyVista"]
    d = date(2027, 12, 24)
    holidays = {d: HolidayInfo("24 de diciembre", "custom", ("custom",))}
    schedule = build_schedule(spec, 2027, holidays)
    target = tmp_path / default_output_filename(spec, 2027)
    generate_excel(spec, schedule, holidays, 2027, "Castilla y León", "Valladolid", target)

    wb = load_workbook(target, data_only=False)
    ws = wb["Easyvista"]
    dates = calendar_dates(2027)
    col = 6 + dates.index(d)
    for row in (3, 4):
        assert ws.cell(row, col).fill.fgColor.rgb in {"00BF8F00", "FFBF8F00"}
    # Y el día sigue siendo descanso en el cuadrante no rotatorio.
    assert ws.cell(5, col).value == "D"
    wb.close()
