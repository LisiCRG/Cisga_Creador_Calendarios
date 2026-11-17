from turnos.catalog import CALENDAR_KEYS, REQUIRED_SHEETS, OUTPUT_BASENAMES


def test_required_sheets_are_stable():
    assert REQUIRED_SHEETS[0] == "INICIO"
    assert REQUIRED_SHEETS[1:] == CALENDAR_KEYS


def test_every_calendar_has_output_name():
    assert set(OUTPUT_BASENAMES) == set(CALENDAR_KEYS)
    assert OUTPUT_BASENAMES["Intensivo"].format(year=2027) == "Calendario_Intensivo_2027_E01.xlsx"
