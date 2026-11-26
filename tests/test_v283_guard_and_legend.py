from datetime import date
from pathlib import Path

import pytest
from openpyxl import load_workbook
from turnos.excel_generator import generate_excel
from turnos.models import CalendarSpec, HolidayInfo, PersonSpec
from turnos.paths import type_template_file
from turnos.scheduler import build_schedule, calendar_dates, is_tt_code, SchedulingError
from turnos.template_reader import load_template

ROOT = Path(__file__).resolve().parents[1]


def _guard_spec(telework='Sí'):
    return CalendarSpec('Supervisores', 'Supervisores', [
        PersonSpec('Guardia', group='G', base_shift='M', telework=telework, start_phase=1 if telework != 'No' else None),
        PersonSpec('Otro', group='G', base_shift='M', telework='Sí', start_phase=2),
    ], {'tt_pattern':['TT','BASE','BASE'], 'guard_anchor':'2026-12-28'}, guard_order=['Guardia'], group_tt_limits={'G':1})


@pytest.mark.parametrize('kind', ['local','regional','national','custom'])
def test_guard_works_holidays_and_keeps_tt(kind):
    d = date(2027,1,1)
    spec = _guard_spec()
    schedule = build_schedule(spec, 2027, {d:HolidayInfo('Festivo',kind,(kind,))})
    assert schedule['Guardia'][d] == 'G_TT'
    assert schedule['Otro'][d] == 'D'
    assert schedule['Guardia'][date(2027,1,2)] == 'G_TT'
    assert schedule['Guardia'][date(2027,1,4)] == 'G'
    assert is_tt_code(schedule['Otro'][date(2027,1,4)])


def test_guard_counts_toward_group_limit():
    spec = _guard_spec()
    spec.people[1].start_phase = 1
    with pytest.raises(SchedulingError, match='máximo'):
        build_schedule(spec,2027,{})


@pytest.mark.parametrize('mode, expected', [('Renuncia','G_TTR'), ('No','G')])
def test_guard_respects_telework_setting(mode,expected):
    spec = _guard_spec(mode)
    assert build_schedule(spec,2027,{})['Guardia'][date(2027,1,1)] == expected


def test_guard_excel_uses_yellow_border(tmp_path):
    spec = _guard_spec()
    d = date(2027,1,1)
    holidays = {d: HolidayInfo('Festivo','national')}
    path = tmp_path/'guard.xlsx'
    generate_excel(spec,build_schedule(spec,2027,holidays),holidays,2027,'Castilla y León','Valladolid',path)
    wb=load_workbook(path)
    cell=wb['Supervisores_OPX'].cell(5,6+calendar_dates(2027).index(d))
    assert cell.value == 'G'
    assert all(getattr(cell.border,side).color.rgb[-6:]=='FFFF00' for side in ('left','right','top','bottom'))
    wb.close()


@pytest.mark.parametrize('key', ['Intensivo','Rotatorio','EasyVista','Puesto Usuario','Farmacia','Sistemas','Supervisores'])
def test_individual_reference_legend(tmp_path,key):
    spec = load_template(ROOT/'templates'/'Plantilla_Cuadrantes_Usuarios_v13.xlsx').calendars[key]
    path=tmp_path/'output.xlsx'
    generate_excel(spec,build_schedule(spec,2027,{}),{},2027,'Castilla y León','Valladolid',path)
    wb=load_workbook(path)
    # v2.8.5: Organización se elimina solo en Sistemas.
    source = load_workbook(type_template_file(key), read_only=True)
    try:
        assert ('Organización' in wb.sheetnames) == (key != 'Sistemas' and 'Organización' in source.sheetnames)
    finally:
        source.close()
    rot=key=='Rotatorio'
    ws=wb['LeyendaROTATORIO' if rot else 'Leyenda']
    assert ('Leyenda' not in wb.sheetnames) if rot else ('LeyendaROTATORIO' not in wb.sheetnames)
    assert ws['A1'].value=='Leyenda'
    assert ws.max_row==(26 if rot else 21)
    assert ws.max_column==(3 if rot else 5)
    assert ws.cell(18 if rot else 11, 3 if rot else 5).value=='Teletrabajo'
    assert ws.cell(18 if rot else 11, 1).border.left.color.rgb[-6:]=='FFFF00'
    assert ws.cell(19 if rot else 12, 1).border.left.color.rgb[-6:]=='FF00FF'
    wb.close()
