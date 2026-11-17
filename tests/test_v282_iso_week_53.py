from datetime import date

from openpyxl import Workbook

from turnos.excel_generator import _write_headers
from turnos.scheduler import calendar_dates, calendar_start


def _week_labels(year: int) -> list[str]:
    dates = calendar_dates(year)
    wb = Workbook()
    ws = wb.active
    _write_headers(ws, dates, {}, 5)
    labels = [ws.cell(2, 5 + week_idx * 7).value for week_idx in range(len(dates) // 7)]
    wb.close()
    return labels


def test_2026_has_real_iso_week_53():
    dates = calendar_dates(2026)
    labels = _week_labels(2026)

    assert calendar_start(2026) == date(2025, 12, 29)
    assert dates[0].isocalendar().week == 1
    assert "SEMANA 53" in labels
    assert labels[52] == "SEMANA 53"


def test_2027_starts_with_iso_week_53_from_2026():
    dates = calendar_dates(2027)
    labels = _week_labels(2027)

    assert calendar_start(2027) == date(2026, 12, 28)
    assert dates[0].isocalendar().year == 2026
    assert dates[0].isocalendar().week == 53
    assert labels[0] == "SEMANA 53"
    assert labels[1] == "SEMANA 1"


def test_future_week_53_transition_is_not_hardcoded_to_2026():
    dates = calendar_dates(2033)
    labels = _week_labels(2033)

    assert calendar_start(2033) == date(2032, 12, 27)
    assert dates[0].isocalendar().year == 2032
    assert dates[0].isocalendar().week == 53
    assert labels[:3] == ["SEMANA 53", "SEMANA 1", "SEMANA 2"]


def test_all_visible_headers_match_iso_week_numbers_for_many_years():
    for year in range(2024, 2051):
        dates = calendar_dates(year)
        labels = _week_labels(year)
        expected = [
            f"SEMANA {dates[week_idx * 7].isocalendar().week}"
            for week_idx in range(len(dates) // 7)
        ]
        assert labels == expected
