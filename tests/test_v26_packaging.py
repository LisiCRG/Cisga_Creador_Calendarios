from pathlib import Path

from turnos.holidays_provider import _spain_calendar

ROOT = Path(__file__).resolve().parents[1]


def test_spec_collects_holidays_resources():
    text = (ROOT / "GENERADOR_TURNOS.spec").read_text(encoding="utf-8")
    assert 'collect_all("holidays")' in text
    assert 'holidays_datas' in text
    assert 'holidays_hiddenimports' in text


def test_holiday_calendar_falls_back_when_spanish_catalog_is_missing():
    calls = []

    class FakeHolidays:
        @staticmethod
        def Spain(**kwargs):
            calls.append(dict(kwargs))
            if kwargs.get("language") == "es":
                raise FileNotFoundError("No translation file found for domain: 'ES'")
            return {"ok": True, "kwargs": kwargs}

    result = _spain_calendar(FakeHolidays, [2027], "CL")
    assert result["ok"] is True
    assert calls[0]["language"] == "es"
    assert "language" not in calls[1]
    assert calls[1]["subdiv"] == "CL"
