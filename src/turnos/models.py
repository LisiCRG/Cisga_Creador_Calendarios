from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class HolidayInfo:
    name: str
    kind: str  # national | regional | local | custom
    scopes: Tuple[str, ...] = ()

    def has_scope(self, scope: str) -> bool:
        return scope == self.kind or scope in self.scopes


@dataclass
class PersonSpec:
    name: str
    group: str = ""
    base_shift: str = ""
    reduced: bool = False
    telework: str = "Sí"  # Sí | Renuncia | No
    tt_pattern: str = ""
    active: bool = True
    start_phase: int | None = None  # fase/orden inicial elegido en plantilla

    @property
    def telework_enabled(self) -> bool:
        return self.telework in {"Sí", "Renuncia"}

    @property
    def telework_renounced(self) -> bool:
        return self.telework == "Renuncia"


@dataclass
class LegendRow:
    values: List[str]


@dataclass
class CalendarSpec:
    key: str
    title: str
    people: List[PersonSpec]
    settings: Dict[str, object] = field(default_factory=dict)
    legend: List[LegendRow] = field(default_factory=list)
    guard_order: List[str] = field(default_factory=list)
    group_tt_limits: Dict[str, int] = field(default_factory=dict)

    @property
    def names(self) -> List[str]:
        return [p.name for p in self.people]


@dataclass
class TemplateModel:
    path: Path
    sheet_order: List[str]
    calendars: Dict[str, CalendarSpec]

    def ordered_calendars(self) -> List[CalendarSpec]:
        return [self.calendars[s] for s in self.sheet_order if s in self.calendars]


Schedule = Dict[str, Dict[date, str]]
