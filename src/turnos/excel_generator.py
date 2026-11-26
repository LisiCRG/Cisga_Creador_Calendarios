from __future__ import annotations

from copy import copy
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.formatting import ConditionalFormattingList
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.properties import CalcProperties

from .catalog import GENERAL_OUTPUT_BASENAME, OUTPUT_BASENAMES
from .models import CalendarSpec, HolidayInfo, Schedule
from .legend_reference import install_legend
from .paths import type_template_file
from .scheduler import calendar_dates, is_tt_code, is_tt_renounced, visible_code

MONTHS_ES = [
    "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
    "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE",
]
MONTHS_TITLE = [m.title() for m in MONTHS_ES]
WEEKDAY_ES = ["L", "M", "X", "J", "V", "S", "D"]
DIAS_VACACIONES_POR_DEFECTO = 23
OPTIONAL_DECEMBER_HOLIDAY_FILL = "BF8F00"  # ocre solicitado para 24/12 y 31/12 opcionales
GENERAL_DEPARTMENT_FILL = "FF0000"

OUTPUT_LAYOUTS = {
    "Intensivo": dict(sheet="Intensivo", name_col=1, vac_cols=[2, 3, 4], cal_start=5, grouped=False, capacity=18),
    "Rotatorio": dict(sheet="Rotatorio", name_col=1, vac_cols=[2, 5, 8], cal_start=11, grouped=False, capacity=13, ndf=True),
    "EasyVista": dict(sheet="Easyvista", group_col=1, name_col=2, vac_cols=[3, 4, 5], cal_start=6, grouped=True, capacity=3),
    "Farmacia": dict(sheet="Farmacia", name_col=1, vac_cols=[2, 3, 4], cal_start=5, grouped=False, capacity=2),
    "Puesto Usuario": dict(sheet="PuestoUsuario", group_col=1, name_col=2, vac_cols=[3, 4, 5], cal_start=6, grouped=True, capacity=3),
    "Sistemas": dict(sheet="SistemasEspecializados", group_col=1, name_col=2, vac_cols=[3, 4, 5], cal_start=6, grouped=True, capacity=8),
    "Supervisores": dict(sheet="Supervisores_OPX", group_col=1, name_col=2, vac_cols=[3, 4, 5], cal_start=6, grouped=True, capacity=15),
}

STYLES = {
    "M":  ("FFCCCC", "990033", False), "M1": ("FFCCCC", "990033", False), "M2": ("FFCCCC", "990033", False),
    "MD": ("FFCCCC", "990033", False), "MF": ("FFCCCC", "990033", False),
    "MA": ("FF7C80", "000000", False),
    "P":  ("44546A", "FFFFFF", True),
    "D":  ("C6EFCE", "006100", False), "V": ("FF0000", "000000", True),
    "C":  ("00B0F0", "000000", True), "B": ("FFC000", "000000", True),
    "A":  ("FFFF00", "000000", True),
    "F1": ("9966FF", "000000", True), "F2": ("9966FF", "000000", True),
    "R":  ("7F7F7F", "FFFFFF", True), "RF": ("7F7F7F", "FFFFFF", True),
    "T":  ("4472C4", "FFFFFF", True), "TD": ("4472C4", "FFFFFF", True), "TF": ("4472C4", "FFFFFF", True),
    "N":  ("FFE699", "806000", False), "ND": ("FFE699", "806000", False), "NF": ("FFE699", "806000", False),
    "G":  ("FF00FF", "FFC000", False),
}


def default_output_filename(spec: CalendarSpec, year: int) -> str:
    return OUTPUT_BASENAMES[spec.key].format(year=year)


def default_general_output_filename(year: int) -> str:
    return GENERAL_OUTPUT_BASENAME.format(year=year)


def _copy_dimension_map(source_dimensions, target_dimensions, target_ws) -> None:
    """Copia SOLO la geometría de filas/columnas, nunca su estilo.

    En Excel una RowDimension/ColumnDimension puede llevar un ``style_id`` que
    se aplica también a celdas todavía no materializadas. Ese identificador es
    local al libro de origen: copiar el objeto Dimension completo a otro
    workbook hacía que el General interpretase ese número con SU tabla de
    estilos, provocando bordes/rellenos fantasma bajo el cuadrante.

    Los estilos visibles de las celdas se copian celda a celda en
    ``_copy_worksheet_content``. Aquí solo necesitamos conservar anchuras,
    alturas, agrupaciones y ocultación.
    """
    for key, dimension in source_dimensions.items():
        target = target_dimensions[key]
        # Propiedades comunes seguras y no ligadas a la tabla de estilos.
        for attr in ("hidden", "outlineLevel", "collapsed"):
            if hasattr(dimension, attr):
                setattr(target, attr, copy(getattr(dimension, attr)))

        # ColumnDimension: un único registro puede abarcar varias columnas
        # (por ejemplo B:D). Conservamos esa geometría, pero no style/customFormat.
        for attr in ("width", "bestFit", "min", "max"):
            if hasattr(dimension, attr):
                setattr(target, attr, copy(getattr(dimension, attr)))

        # RowDimension.
        for attr in ("height", "thickTop", "thickBottom"):
            if hasattr(dimension, attr):
                setattr(target, attr, copy(getattr(dimension, attr)))


def _copy_worksheet_content(source_ws, target_ws) -> None:
    """Copia una hoja de calendario a otro libro conservando su aspecto.

    openpyxl solo permite copy_worksheet dentro del mismo Workbook. Esta
    rutina copia lo necesario para los calendarios generados: valores,
    fórmulas, estilos, combinaciones, dimensiones y configuración de impresión.
    """
    target_ws.sheet_format = copy(source_ws.sheet_format)
    target_ws.sheet_properties = copy(source_ws.sheet_properties)
    # sheet_view es una propiedad de solo lectura en openpyxl; copiamos
    # explícitamente los atributos visuales relevantes.
    for attr in (
        "showGridLines", "showRowColHeaders", "showZeros", "rightToLeft",
        "zoomScale", "zoomScaleNormal", "zoomScalePageLayoutView",
        "zoomScaleSheetLayoutView", "view",
    ):
        if hasattr(source_ws.sheet_view, attr):
            setattr(target_ws.sheet_view, attr, copy(getattr(source_ws.sheet_view, attr)))
    target_ws.freeze_panes = source_ws.freeze_panes
    target_ws.sheet_state = "visible"
    target_ws.protection = copy(source_ws.protection)
    target_ws.print_options = copy(source_ws.print_options)
    target_ws.page_margins = copy(source_ws.page_margins)
    target_ws.page_setup = copy(source_ws.page_setup)
    target_ws.oddHeader = copy(source_ws.oddHeader)
    target_ws.oddFooter = copy(source_ws.oddFooter)
    target_ws.evenHeader = copy(source_ws.evenHeader)
    target_ws.evenFooter = copy(source_ws.evenFooter)
    target_ws.firstHeader = copy(source_ws.firstHeader)
    target_ws.firstFooter = copy(source_ws.firstFooter)

    _copy_dimension_map(source_ws.row_dimensions, target_ws.row_dimensions, target_ws)
    _copy_dimension_map(source_ws.column_dimensions, target_ws.column_dimensions, target_ws)

    for row in source_ws.iter_rows():
        for source_cell in row:
            target_cell = target_ws.cell(row=source_cell.row, column=source_cell.column)
            target_cell.value = source_cell.value
            if source_cell.has_style:
                # No se copia _style directamente entre workbooks: sus índices
                # apuntan a las tablas de estilos del libro origen. Asignando los
                # componentes, openpyxl registra correctamente el estilo en el
                # libro General.
                target_cell.font = copy(source_cell.font)
                target_cell.fill = copy(source_cell.fill)
                target_cell.border = copy(source_cell.border)
                target_cell.alignment = copy(source_cell.alignment)
                target_cell.number_format = source_cell.number_format
                target_cell.protection = copy(source_cell.protection)
            if source_cell.hyperlink:
                target_cell._hyperlink = copy(source_cell.hyperlink)
            if source_cell.comment:
                target_cell.comment = copy(source_cell.comment)

    for merged in source_ws.merged_cells.ranges:
        target_ws.merge_cells(str(merged))

    # Las hojas de calendario finales no usan validaciones, tablas ni gráficos,
    # pero se conserva el autofiltro y la configuración de impresión por si una
    # plantilla futura los incorpora.
    target_ws.auto_filter = copy(source_ws.auto_filter)
    try:
        target_ws.print_area = source_ws.print_area
    except Exception:
        pass
    try:
        target_ws.print_title_rows = source_ws.print_title_rows
        target_ws.print_title_cols = source_ws.print_title_cols
    except Exception:
        pass


def _legend_rows_from_workbook(source_wb) -> list[tuple]:
    """Devuelve las filas útiles de la Leyenda, sin título/cabecera/vacíos."""
    if "Leyenda" not in source_wb.sheetnames:
        return []
    ws = source_wb["Leyenda"]
    result = []
    for row in ws.iter_rows(min_row=3, max_col=5, values_only=True):
        values = tuple(row[:5])
        if any(value not in (None, "") for value in values):
            result.append(values)
    return result


def _write_general_legend(wb, legend_entries, selected_titles: list[str]) -> None:
    """Crea una única leyenda CAU, deduplicada y con ámbito por departamento."""
    if "Leyenda" in wb.sheetnames:
        del wb["Leyenda"]
    ws = wb.create_sheet("Leyenda")
    ws.sheet_view.showGridLines = False

    ws.merge_cells("A1:F1")
    ws["A1"] = "LEYENDA GENERAL · CAU"
    ws["A1"].fill = PatternFill("solid", fgColor="1F4E78")
    ws["A1"].font = Font(color="FFFFFF", bold=True, size=13)
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")

    headers = ["Departamento(s)", "Código / marca", "Significado", "Horario / uso", "Formato", "Cuenta"]
    for c, header in enumerate(headers, 1):
        cell = ws.cell(2, c)
        cell.value = header
        cell.fill = PatternFill("solid", fgColor="4472C4")
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    all_titles = list(dict.fromkeys(selected_titles))
    for r, (values, departments) in enumerate(legend_entries, 3):
        deps = list(dict.fromkeys(departments))
        scope = "Todos" if all_titles and set(deps) == set(all_titles) else ", ".join(deps)
        row_values = [scope, *values]
        for c, value in enumerate(row_values, 1):
            cell = ws.cell(r, c)
            cell.value = value
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            if r % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="F2F2F2")

    widths = {"A": 34, "B": 22, "C": 34, "D": 34, "E": 18, "F": 14}
    for col, width in widths.items():
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A3"


def _copy_aux_sheet(source_ws, wb, title: str):
    """Copia una hoja auxiliar evitando estilos de dimensión entre workbooks."""
    if title in wb.sheetnames:
        del wb[title]
    target_ws = wb.create_sheet(title=title)
    _copy_worksheet_content(source_ws, target_ws)
    return target_ws


def _copy_cell_components(source_cell, target_cell, *, copy_value: bool = True) -> None:
    """Copia valor y aspecto de una celda entre workbooks sin reutilizar style_id."""
    if copy_value:
        target_cell.value = source_cell.value
    if source_cell.has_style:
        target_cell.font = copy(source_cell.font)
        target_cell.fill = copy(source_cell.fill)
        target_cell.border = copy(source_cell.border)
        target_cell.alignment = copy(source_cell.alignment)
        target_cell.number_format = source_cell.number_format
        target_cell.protection = copy(source_cell.protection)
    if source_cell.hyperlink:
        target_cell._hyperlink = copy(source_cell.hyperlink)
    if source_cell.comment:
        target_cell.comment = copy(source_cell.comment)


def _copy_general_calendar_header(source_ws, target_ws, source_cal_start: int, target_row: int, target_cal_start: int, day_count: int) -> None:
    """Copia las cuatro filas de cabecera del calendario desplazadas al bloque General."""
    source_last = source_cal_start + day_count - 1
    target_last = target_cal_start + day_count - 1

    # Celdas de fecha/semana/mes. Los dos primeros campos del General se
    # reservan siempre para Subdepartamento y Operador.
    for src_row in range(1, 5):
        dst_row = target_row + src_row - 1
        target_ws.row_dimensions[dst_row].height = source_ws.row_dimensions[src_row].height
        for offset in range(day_count):
            _copy_cell_components(
                source_ws.cell(src_row, source_cal_start + offset),
                target_ws.cell(dst_row, target_cal_start + offset),
            )

    # Reproducimos únicamente las combinaciones de la cabecera calendario,
    # desplazándolas a la zona C:... del General.
    for merged in source_ws.merged_cells.ranges:
        if merged.min_row < 1 or merged.max_row > 4:
            continue
        if merged.max_col < source_cal_start or merged.min_col > source_last:
            continue
        if merged.min_col < source_cal_start or merged.max_col > source_last:
            continue
        row1 = target_row + merged.min_row - 1
        row2 = target_row + merged.max_row - 1
        col1 = target_cal_start + (merged.min_col - source_cal_start)
        col2 = target_cal_start + (merged.max_col - source_cal_start)
        target_ws.merge_cells(start_row=row1, start_column=col1, end_row=row2, end_column=col2)

    # A/B forman la zona normalizada del General. No se reintroducen las
    # columnas DIAS VAC. / DISFRUTADOS / PENDIENTES.
    target_ws.cell(target_row + 3, 1).value = "SUBDEPARTAMENTO"
    target_ws.cell(target_row + 3, 2).value = "OPERADOR"
    # Usamos el estilo del encabezado de día para no introducir un formato
    # nuevo ajeno a los calendarios existentes.
    proto = source_ws.cell(4, source_cal_start)
    for col in (1, 2):
        _copy_cell_components(proto, target_ws.cell(target_row + 3, col), copy_value=False)
        target_ws.cell(target_row + 3, col).font = copy(proto.font)
        target_ws.cell(target_row + 3, col).font = Font(
            name=proto.font.name,
            size=proto.font.sz,
            bold=True,
            italic=proto.font.italic,
            vertAlign=proto.font.vertAlign,
            underline=proto.font.underline,
            strike=proto.font.strike,
            color=copy(proto.font.color),
        )
        target_ws.cell(target_row + 3, col).alignment = Alignment(horizontal="center", vertical="center")


def _general_group_spans(spec: CalendarSpec) -> list[tuple[int, int, str]]:
    """Devuelve tramos contiguos de subdepartamento en el orden de la plantilla."""
    if not spec.people:
        return []
    if not OUTPUT_LAYOUTS[spec.key].get("grouped"):
        return [(0, len(spec.people) - 1, spec.title)]
    spans = []
    start = 0
    current = spec.people[0].group or spec.title
    for idx, person in enumerate(spec.people[1:], 1):
        group = person.group or spec.title
        if group != current:
            spans.append((start, idx - 1, current))
            start = idx
            current = group
    spans.append((start, len(spec.people) - 1, current))
    return spans


def _group_style_source_cell(source_ws, layout: dict, source_row: int):
    """Obtiene una celda real que represente el estilo de subdepartamento."""
    if layout.get("grouped"):
        group_col = int(layout["group_col"])
        cell = source_ws.cell(source_row, group_col)
        # Si la fila está dentro de un merge, el estilo útil es el top-left.
        for merged in source_ws.merged_cells.ranges:
            if merged.min_col == group_col == merged.max_col and merged.min_row <= source_row <= merged.max_row:
                return source_ws.cell(merged.min_row, group_col)
        return cell
    # Los departamentos sin subdepartamento reutilizan el estilo de su columna
    # de nombres; solo se añade la nueva columna A para alinear todos los bloques.
    return source_ws.cell(source_row, int(layout["name_col"]))


def _write_general_department_block(
    target_ws,
    spec: CalendarSpec,
    source_ws,
    layout: dict,
    start_row: int,
    day_count: int,
    day_width: float,
    operator_row_height: float | None,
) -> int:
    """Escribe un departamento completo en la hoja General y devuelve la siguiente fila libre."""
    target_cal_start = 3  # A=subdepartamento, B=operador, C...=calendario
    target_last_col = target_cal_start + day_count - 1

    # Separador de departamento solicitado: rojo, negrita, hasta el último día.
    for col in range(1, target_last_col + 1):
        cell = target_ws.cell(start_row, col)
        cell.fill = PatternFill("solid", fgColor=GENERAL_DEPARTMENT_FILL)
        cell.font = Font(bold=True, color="000000")
    target_ws.cell(start_row, 1).value = spec.title

    header_row = start_row + 1
    source_cal_start = int(layout["cal_start"])
    _copy_general_calendar_header(source_ws, target_ws, source_cal_start, header_row, target_cal_start, day_count)

    first_person_row = header_row + 4
    source_first_person_row = 5

    # Nombre + días. No copiamos las columnas de vacaciones ni el bloque N/D/F
    # inferior de Rotatorio.
    for idx, person in enumerate(spec.people):
        src_row = source_first_person_row + idx
        dst_row = first_person_row + idx
        if operator_row_height is not None:
            target_ws.row_dimensions[dst_row].height = operator_row_height
        elif source_ws.row_dimensions[src_row].height is not None:
            target_ws.row_dimensions[dst_row].height = source_ws.row_dimensions[src_row].height

        src_name = source_ws.cell(src_row, int(layout["name_col"]))
        dst_name = target_ws.cell(dst_row, 2)
        _copy_cell_components(src_name, dst_name)
        dst_name.value = person.name

        for offset in range(day_count):
            _copy_cell_components(
                source_ws.cell(src_row, source_cal_start + offset),
                target_ws.cell(dst_row, target_cal_start + offset),
            )

    # Columna A: conserva subdepartamentos reales y crea uno para los tres
    # departamentos que históricamente no lo tenían.
    for span_start, span_end, label in _general_group_spans(spec):
        dst_start = first_person_row + span_start
        dst_end = first_person_row + span_end
        style_source = _group_style_source_cell(source_ws, layout, source_first_person_row + span_start)
        for row in range(dst_start, dst_end + 1):
            _copy_cell_components(style_source, target_ws.cell(row, 1), copy_value=False)
        target_ws.cell(dst_start, 1).value = label
        target_ws.cell(dst_start, 1).font = copy(style_source.font)
        target_ws.cell(dst_start, 1).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        if dst_end > dst_start:
            target_ws.merge_cells(start_row=dst_start, start_column=1, end_row=dst_end, end_column=1)

    # Todas las columnas de días tienen exactamente la misma anchura en todos
    # los bloques, para que el calendario quede perfectamente alineado.
    for col in range(target_cal_start, target_last_col + 1):
        target_ws.column_dimensions[get_column_letter(col)].width = day_width

    # Una fila en blanco separa visualmente departamentos. El siguiente bloque
    # empieza después de ella con su propia fila roja de departamento.
    return first_person_row + len(spec.people) + 1


def generate_general_excel(
    generated_calendars: List[Tuple[CalendarSpec, Path]],
    year: int,
    output_path: Path,
) -> Path:
    """Crea el General CAU con todos los calendarios en una única hoja.

    La hoja ``General`` normaliza todos los bloques a:
      A = Subdepartamento
      B = Operador
      C... = días

    Se eliminan las columnas de vacaciones y el resumen mensual N/D/F de
    Rotatorio. Leyenda y Festivos permanecen como hojas únicas.
    """
    if not generated_calendars:
        raise ValueError("No hay calendarios generados para crear el General CAU.")

    wb = Workbook()
    ws_general = wb.active
    ws_general.title = "General"
    ws_general.sheet_view.showGridLines = False
    wb.calculation = CalcProperties(calcMode="auto", fullCalcOnLoad=True, forceFullCalc=True, calcOnSave=True)

    general_theme_loaded = False
    holiday_source = None
    legend_map = {}
    legend_order = []
    selected_titles = []
    day_count = len(calendar_dates(year))
    common_day_width = None
    common_operator_height = None
    current_row = 1

    # Anchuras estables para las dos columnas descriptivas.
    ws_general.column_dimensions["A"].width = 22
    ws_general.column_dimensions["B"].width = 35

    for spec, source_path in generated_calendars:
        layout = OUTPUT_LAYOUTS[spec.key]
        source_wb = load_workbook(source_path, data_only=False)
        selected_titles.append(spec.title)

        if not general_theme_loaded:
            wb.loaded_theme = source_wb.loaded_theme
            if hasattr(source_wb, "_colors"):
                wb._colors = copy(source_wb._colors)
            general_theme_loaded = True

        source_sheet_name = layout["sheet"]
        if source_sheet_name not in source_wb.sheetnames:
            source_wb.close()
            raise ValueError(
                f"El calendario {source_path.name} no contiene la hoja {source_sheet_name!r}."
            )
        source_ws = source_wb[source_sheet_name]
        source_cal_start = int(layout["cal_start"])

        if common_day_width is None:
            # Las plantillas usan una anchura base estrecha para los días.
            # Acceder a column_dimensions[letra] cuando no existe un registro
            # explícito crea una dimensión con width=13, que ensancha el General.
            # Tomamos por tanto el ancho base real de la hoja individual.
            common_day_width = source_ws.sheet_format.defaultColWidth or 3.71
        if common_operator_height is None:
            common_operator_height = source_ws.row_dimensions[5].height or 15.95

        current_row = _write_general_department_block(
            ws_general,
            spec,
            source_ws,
            layout,
            current_row,
            day_count,
            float(common_day_width),
            float(common_operator_height),
        )

        holiday_name = next((name for name in source_wb.sheetnames if name.startswith("Festivos ")), None)
        if holiday_source is None and holiday_name:
            holiday_source = (source_path, holiday_name)

        # El General mantiene su leyenda semántica original (no la referencia visual).
        for values in (tuple((legend.values + [""] * 5)[:5]) for legend in spec.legend):
            values = tuple(value if value != "" else None for value in values)
            if not any(value is not None for value in values):
                continue
            if values not in legend_map:
                legend_map[values] = []
                legend_order.append(values)
            if spec.title not in legend_map[values]:
                legend_map[values].append(spec.title)

        source_wb.close()

    # No hay columnas de vacaciones ni fórmulas resumen en la hoja General.
    # El área imprimible queda ceñida al contenido real del conjunto.
    last_day_col = 2 + day_count
    ws_general.print_area = f"A1:{get_column_letter(last_day_col)}{max(1, current_row - 1)}"

    legend_entries = [(values, legend_map[values]) for values in legend_order]
    _write_general_legend(wb, legend_entries, selected_titles)

    if holiday_source is not None:
        holiday_path, holiday_name = holiday_source
        holiday_wb = load_workbook(holiday_path, data_only=False)
        _copy_aux_sheet(holiday_wb[holiday_name], wb, f"Festivos {year}")
        holiday_wb.close()
    else:
        wb.create_sheet(f"Festivos {year}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return output_path

def _copy_row_style(ws, source_row: int, target_row: int, max_col: int) -> None:
    for col in range(1, max_col + 1):
        src = ws.cell(source_row, col)
        dst = ws.cell(target_row, col)
        if src.has_style:
            dst._style = copy(src._style)
        dst.number_format = src.number_format
        dst.alignment = copy(src.alignment)
        dst.protection = copy(src.protection)
    ws.row_dimensions[target_row].height = ws.row_dimensions[source_row].height


def _style_border(day_index: int) -> Border:
    thin = Side(style="thin", color="000000")
    medium = Side(style="medium", color="000000")
    return Border(
        left=medium if day_index % 7 == 0 else thin,
        right=medium if day_index % 7 == 6 else thin,
        top=thin, bottom=thin,
    )


def _resolve_alias(code: str, aliases: dict[str, str] | None = None) -> str:
    cur = str(code or "").upper()
    mapping = {str(k).upper(): str(v).upper() for k, v in dict(aliases or {}).items()}
    seen = set()
    while cur in mapping and cur not in seen:
        seen.add(cur)
        cur = mapping[cur]
    return cur


def _style_for_code(code: str, aliases: dict[str, str] | None = None) -> tuple[str, str, bool]:
    """Devuelve estilo; los turnos creados heredan el color de su turno padre."""
    code = str(code or "").upper()
    if code in STYLES:
        return STYLES[code]
    family = _resolve_alias(code, aliases)
    if family in STYLES:
        return STYLES[family]
    for candidate in (family, code):
        if candidate.startswith("MA"):
            return STYLES["MA"]
        if candidate.startswith("M"):
            return STYLES["M"]
        if candidate.startswith("T"):
            return STYLES["T"]
        if candidate.startswith("N"):
            return STYLES["N"]
        if candidate.startswith("R"):
            return STYLES["R"]
        if candidate.startswith("F"):
            return STYLES["F1"]
    return ("E7E6E6", "000000", False)


def _apply_shift_style(cell, internal_code: str, day_index: int, aliases: dict[str, str] | None = None) -> None:
    code = visible_code(internal_code)
    # En Rotatorio un turno creado puede verse como X1D/X1F; para estilo heredado
    # primero se prueba el código exacto y después el código sin sufijo D/F.
    style_code = code
    if code not in STYLES and code.endswith(("D", "F")):
        style_code = code[:-1]
    fill, font, bold = _style_for_code(style_code, aliases)
    cell.fill = PatternFill("solid", fgColor=fill)
    cell.font = Font(name="Calibri", size=8, color=font, bold=bold)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    if is_tt_code(internal_code):
        color = "FF00FF" if is_tt_renounced(internal_code) else "FFFF00"
        side = Side(style="thick", color=color)
        cell.border = Border(left=side, right=side, top=side, bottom=side)
    else:
        cell.border = _style_border(day_index)

def _month_segments(dates: List[date]) -> List[Tuple[int, int, int]]:
    out = []
    start = 0
    month = dates[0].month
    for i, d in enumerate(dates[1:], 1):
        if d.month != month:
            out.append((start, i - 1, month))
            start, month = i, d.month
    out.append((start, len(dates) - 1, month))
    return out


def _unmerge_headers(ws, cal_start: int) -> None:
    for merged in list(ws.merged_cells.ranges):
        if merged.min_row <= 2 and merged.max_row <= 2 and merged.max_col >= cal_start:
            ws.unmerge_cells(str(merged))


def _write_headers(ws, dates: List[date], holidays: Dict[date, HolidayInfo], cal_start: int) -> None:
    normal_col = cal_start
    sat_col = cal_start + 5
    sun_col = cal_start + 6
    jan1_offset = (date(2026, 1, 1) - date(2025, 12, 29)).days
    jan1_col = cal_start + jan1_offset
    local_offset = (date(2026, 5, 13) - date(2025, 12, 29)).days
    local_col = cal_start + local_offset

    styles = {
        "month": copy(ws.cell(1, normal_col)._style),
        "week": copy(ws.cell(2, normal_col)._style),
        "day": copy(ws.cell(3, normal_col)._style),
        "weekday": copy(ws.cell(4, normal_col)._style),
        "sat": copy(ws.cell(4, sat_col)._style),
        "sun": copy(ws.cell(4, sun_col)._style),
        "holiday_day": copy(ws.cell(3, jan1_col)._style),
        "holiday_weekday": copy(ws.cell(4, jan1_col)._style),
        "local_day": copy(ws.cell(3, local_col)._style),
        "local_weekday": copy(ws.cell(4, local_col)._style),
    }
    _unmerge_headers(ws, cal_start)
    max_col = cal_start + len(dates) - 1
    for row in range(1, 5):
        for col in range(cal_start, max_col + 1):
            ws.cell(row, col).value = None

    for s, e, month in _month_segments(dates):
        c1, c2 = cal_start + s, cal_start + e
        ws.merge_cells(start_row=1, start_column=c1, end_row=1, end_column=c2)
        ws.cell(1, c1).value = MONTHS_ES[month - 1]
        ws.cell(1, c1)._style = copy(styles["month"])
        ws.cell(1, c1).alignment = Alignment(horizontal="center", vertical="center")

    for week_idx in range(len(dates) // 7):
        c1 = cal_start + week_idx * 7
        c2 = c1 + 6
        ws.merge_cells(start_row=2, start_column=c1, end_row=2, end_column=c2)
        iso_week = dates[week_idx * 7].isocalendar().week
        ws.cell(2, c1).value = f"SEMANA {iso_week}"
        ws.cell(2, c1)._style = copy(styles["week"])
        ws.cell(2, c1).alignment = Alignment(horizontal="center", vertical="center")

    for i, d in enumerate(dates):
        col = cal_start + i
        day_cell, wd_cell = ws.cell(3, col), ws.cell(4, col)
        day_cell.value, wd_cell.value = d.day, WEEKDAY_ES[d.weekday()]
        info = holidays.get(d)
        if info and info.has_scope("custom"):
            # 24/12 y 31/12 opcionales: se comportan como festivo, pero su
            # cabecera se distingue en ocre. Se conserva el resto del estilo
            # de festivo (fuente, bordes y alineación).
            day_cell._style = copy(styles["holiday_day"])
            wd_cell._style = copy(styles["holiday_weekday"])
            day_cell.fill = PatternFill("solid", fgColor=OPTIONAL_DECEMBER_HOLIDAY_FILL)
            wd_cell.fill = PatternFill("solid", fgColor=OPTIONAL_DECEMBER_HOLIDAY_FILL)
        elif info and info.kind == "local":
            day_cell._style = copy(styles["local_day"])
            wd_cell._style = copy(styles["local_weekday"])
        elif info:
            day_cell._style = copy(styles["holiday_day"])
            wd_cell._style = copy(styles["holiday_weekday"])
        else:
            day_cell._style = copy(styles["day"])
            wd_cell._style = copy(styles["sat"] if d.weekday() == 5 else styles["sun"] if d.weekday() == 6 else styles["weekday"])


def _contiguous_runs(columns: List[int]) -> List[Tuple[int, int]]:
    if not columns:
        return []
    cols = sorted(columns)
    out = []
    start = prev = cols[0]
    for col in cols[1:]:
        if col == prev + 1:
            prev = col
        else:
            out.append((start, prev))
            start = prev = col
    out.append((start, prev))
    return out


def _row_count_formula(row: int, dates: List[date], target_year: int, code: str, cal_start: int) -> str:
    cols = [cal_start + i for i, d in enumerate(dates) if d.year == target_year]
    terms = []
    for c1, c2 in _contiguous_runs(cols):
        terms.append(f'COUNTIF({get_column_letter(c1)}{row}:{get_column_letter(c2)}{row},"{code}")')
    return "=" + "+".join(terms) if terms else "=0"


def _unmerge_groups(ws, group_col: int, start_row: int) -> None:
    for merged in list(ws.merged_cells.ranges):
        if merged.min_col == group_col == merged.max_col and merged.min_row >= start_row:
            ws.unmerge_cells(str(merged))


def _unmerge_operator_area(ws, start_row: int, end_row: int, max_col: int) -> None:
    """Elimina combinaciones que cruzan el área editable de trabajadores.

    Algunas plantillas tipo contienen celdas combinadas heredadas dentro de
    las filas de operadores. openpyxl representa las celdas secundarias como
    MergedCell y no permite escribir en ellas. Antes de limpiar/escribir las
    filas de trabajadores descombinamos únicamente los rangos que intersectan
    esa zona; las cabeceras de meses/semanas (filas 1-4) no se tocan.
    """
    for merged in list(ws.merged_cells.ranges):
        intersects_rows = not (merged.max_row < start_row or merged.min_row > end_row)
        intersects_cols = not (merged.max_col < 1 or merged.min_col > max_col)
        if intersects_rows and intersects_cols:
            ws.unmerge_cells(str(merged))


def _prepare_operator_area(ws, spec: CalendarSpec, layout: dict, dates: List[date]) -> None:
    start = 5
    count = len(spec.people)
    capacity = int(layout["capacity"])
    cal_start = int(layout["cal_start"])
    max_col = cal_start + len(dates) - 1
    clear_rows = max(capacity, count)
    # Evita errores ``MergedCell object attribute value is read-only`` al
    # reutilizar las plantillas visuales originales.
    _unmerge_operator_area(ws, start, start + clear_rows - 1, max_col)
    if layout.get("grouped"):
        _unmerge_groups(ws, int(layout["group_col"]), start)

    # Rotatorio tiene el resumen N/D/F debajo. Lo limpiamos antes de permitir más filas.
    if layout.get("ndf"):
        ndf_start = start + count + 1
        ndf_end = max(ws.max_row, start + count + 80)
        _unmerge_operator_area(ws, ndf_start, ndf_end, 10)
        for r in range(ndf_start, ndf_end + 1):
            for c in range(1, 11):
                ws.cell(r, c).value = None

    for i in range(clear_rows):
        row = start + i
        if i >= capacity:
            _copy_row_style(ws, start, row, max_col)
        # Limpia columnas de identificación, vacaciones y calendario.
        for c in range(1, cal_start):
            ws.cell(row, c).value = None
        for c in range(cal_start, max_col + 1):
            ws.cell(row, c).value = None
        if layout.get("ndf") and i == count:
            # Reserva una línea visible en blanco entre el último agente y N/D/F.
            # Debe quedar completamente limpia: al desplazar el bloque según el
            # número real de agentes no podemos heredar bordes/rellenos de una
            # antigua fila de operador de la plantilla tipo.
            for c in range(1, max_col + 1):
                cell = ws.cell(row, c)
                cell._style = None
                cell.number_format = "General"
                cell.alignment = Alignment()
                cell.protection = copy(ws.cell(1, 1).protection)
            ws.row_dimensions[row].hidden = False
            ws.row_dimensions[row].height = 15
        else:
            ws.row_dimensions[row].hidden = i >= count

    if layout.get("grouped"):
        group_col = int(layout["group_col"])
        blocks = []
        block_start = start
        current = None
        for idx, p in enumerate(spec.people):
            group = p.group or spec.title.upper()
            if current is None:
                current = group
                block_start = start + idx
            elif group != current:
                blocks.append((current, block_start, start + idx - 1))
                current, block_start = group, start + idx
        if current is not None:
            blocks.append((current, block_start, start + count - 1))
        for group, r1, r2 in blocks:
            ws.cell(r1, group_col).value = group
            if r2 > r1:
                ws.merge_cells(start_row=r1, start_column=group_col, end_row=r2, end_column=group_col)
            # Los subdepartamentos se muestran en orientación normal/horizontal.
            ws.cell(r1, group_col).alignment = Alignment(horizontal="center", vertical="center", text_rotation=0, wrap_text=True)
        # Evita que los nombres de subdepartamento queden excesivamente estrechos
        # al pasar de texto vertical a horizontal.
        letter = get_column_letter(group_col)
        current_width = ws.column_dimensions[letter].width or 0
        if current_width < 20:
            ws.column_dimensions[letter].width = 20


def _write_people(ws, spec: CalendarSpec, schedule: Schedule, year: int, dates: List[date], layout: dict) -> None:
    start = 5
    name_col = int(layout["name_col"])
    vac_cols = [int(x) for x in layout["vac_cols"]]
    cal_start = int(layout["cal_start"])

    for idx, p in enumerate(spec.people):
        row = start + idx
        ws.cell(row, name_col).value = p.name
        ws.cell(row, vac_cols[0]).value = DIAS_VACACIONES_POR_DEFECTO
        ws.cell(row, vac_cols[1]).value = _row_count_formula(row, dates, year, "V", cal_start)
        a, b = get_column_letter(vac_cols[0]), get_column_letter(vac_cols[1])
        ws.cell(row, vac_cols[2]).value = f"={a}{row}-{b}{row}"
        for day_idx, d in enumerate(dates):
            internal = schedule[p.name][d]
            cell = ws.cell(row, cal_start + day_idx)
            cell.value = visible_code(internal)
            _apply_shift_style(cell, internal, day_idx, spec.settings.get("shift_aliases", {}))

    ws.freeze_panes = f"{get_column_letter(cal_start)}{start}"
    ws.sheet_view.showGridLines = False



def _restore_rotatorio_vacation_merges(ws, spec: CalendarSpec) -> None:
    """Restaura el diseño original del Rotatorio en las filas de agentes.

    B:D = DÍAS VAC., E:G = DISFRUTADOS, H:J = PENDIENTES. La preparación
    de la hoja debe descombinar primero estas celdas para evitar MergedCell
    al limpiar/escribir; una vez escritos los valores se vuelven a combinar
    para que el bloque N/D/F inferior quede alineado exactamente con B:J.
    """
    for idx, _person in enumerate(spec.people):
        row = 5 + idx
        for c1, c2 in ((2, 4), (5, 7), (8, 10)):
            ws.merge_cells(start_row=row, start_column=c1, end_row=row, end_column=c2)
            ws.cell(row, c1).alignment = Alignment(horizontal="center", vertical="center")


def _write_holidays(wb, year: int, community: str, holidays: Dict[date, HolidayInfo]) -> None:
    old = next((s for s in wb.sheetnames if s.startswith("Festivos ")), None)
    if old:
        ws = wb[old]
        ws.title = f"Festivos {year}"
    else:
        ws = wb.create_sheet(f"Festivos {year}")
    # Algunas plantillas originales combinan celdas en la hoja Festivos.
    # Descombinamos cualquier rango que toque A:B antes de limpiar para no
    # intentar escribir sobre objetos MergedCell de solo lectura.
    for merged in list(ws.merged_cells.ranges):
        if merged.min_col <= 2 and merged.max_col >= 1:
            ws.unmerge_cells(str(merged))
    # Preserva el aspecto general, pero reconstruye los valores de A:B.
    for r in range(1, max(ws.max_row, 30) + 1):
        ws.cell(r, 1).value = None
        ws.cell(r, 2).value = None
    ws["A1"] = f"Calendario laboral de {community} {year}"
    ws["A2"], ws["B2"] = "Día", "Festividad"
    rows = sorted((d, h) for d, h in holidays.items() if d.year == year)
    months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    for r, (d, info) in enumerate(rows, 3):
        ws.cell(r, 1).value = f"{d.day} de {months[d.month - 1]}"
        ws.cell(r, 2).value = info.name


def _write_legend(wb, spec: CalendarSpec) -> None:
    ws = wb["Leyenda"] if "Leyenda" in wb.sheetnames else wb.create_sheet("Leyenda")
    for merged in list(ws.merged_cells.ranges):
        if merged.min_row <= 40:
            ws.unmerge_cells(str(merged))
    for r in range(1, max(ws.max_row, 40) + 1):
        for c in range(1, 6):
            ws.cell(r, c).value = None
    ws.merge_cells("A1:E1")
    ws["A1"] = f"LEYENDA · {spec.title}"
    ws["A1"].fill = PatternFill("solid", fgColor="1F4E78")
    ws["A1"].font = Font(color="FFFFFF", bold=True, size=13)
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")
    headers = ["Código / marca", "Significado", "Horario / uso", "Formato", "Cuenta"]
    for c, h in enumerate(headers, 1):
        cell = ws.cell(2, c)
        cell.value = h
        cell.fill = PatternFill("solid", fgColor="4472C4")
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(horizontal="center")
    for r, legend in enumerate(spec.legend, 3):
        for c, value in enumerate((legend.values + [""] * 5)[:5], 1):
            ws.cell(r, c).value = value
            ws.cell(r, c).alignment = Alignment(vertical="center", wrap_text=True)
    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 28
    ws.column_dimensions["C"].width = 28
    ws.column_dimensions["D"].width = 18
    ws.column_dimensions["E"].width = 14
    ws.sheet_view.showGridLines = False


def _accounting_months(dates: List[date], year: int) -> List[int]:
    result = [0] * len(dates)
    for start in range(0, len(dates), 7):
        week = dates[start:start + 7]
        latest = week[-1]
        assigned = latest.month if latest.year == year else 0
        for i in range(len(week)):
            result[start + i] = assigned
    return result


def _write_tt_conteo(wb, spec: CalendarSpec, schedule: Schedule, dates: List[date], year: int) -> None:
    # Solo se crea si existe alguna asignación TT/renuncia.
    if not any(is_tt_code(schedule[n][d]) for n in spec.names for d in dates):
        for stale in ("Conteo", "_MetaConteo"):
            if stale in wb.sheetnames:
                del wb[stale]
        return
    for stale in ("Conteo", "_MetaConteo"):
        if stale in wb.sheetnames:
            del wb[stale]
    meta = wb.create_sheet("_MetaConteo")
    months = _accounting_months(dates, year)
    for i, d in enumerate(dates, 1):
        meta.cell(1, i).value = d.isoformat()
        meta.cell(2, i).value = months[i - 1]
    for idx, name in enumerate(spec.names, 4):
        for i, d in enumerate(dates, 1):
            meta.cell(idx, i).value = 1 if is_tt_code(schedule[name][d]) else 0
    meta.sheet_state = "hidden"

    ws = wb.create_sheet("Conteo")
    headers = [("Supervisor" if spec.key == "Supervisores" else "Agente"), *MONTHS_TITLE, "Total"]
    for c, h in enumerate(headers, 1):
        ws.cell(1, c).value = h
        ws.cell(1, c).fill = PatternFill("solid", fgColor="4472C4")
        ws.cell(1, c).font = Font(color="FFFFFF", bold=True)
        ws.cell(1, c).alignment = Alignment(horizontal="center")
    cols_by_month = {m: [] for m in range(1, 13)}
    for idx, m in enumerate(months, 1):
        if m:
            cols_by_month[m].append(idx)
    for r_idx, name in enumerate(spec.names, 2):
        ws.cell(r_idx, 1).value = name
        meta_row = r_idx + 2
        for m in range(1, 13):
            terms = []
            for c1, c2 in _contiguous_runs(cols_by_month[m]):
                terms.append(f"SUM('_MetaConteo'!{get_column_letter(c1)}{meta_row}:{get_column_letter(c2)}{meta_row})")
            ws.cell(r_idx, m + 1).value = "=" + "+".join(terms) if terms else "=0"
        ws.cell(r_idx, 14).value = f"=SUM(B{r_idx}:M{r_idx})"
    ws["P1"], ws["Q1"] = "Regla TT", "Borde amarillo = acepta; magenta = renuncia. Ambos cuentan como plaza TT."
    ws["P2"], ws["Q2"] = "Regla mensual", "Si una semana toca dos meses, toda la semana se imputa al mes más nuevo."
    ws.column_dimensions["A"].width = 32
    for c in range(2, 15):
        ws.column_dimensions[get_column_letter(c)].width = 11
    ws.column_dimensions["Q"].width = 78
    ws.freeze_panes = "B2"
    ws.sheet_view.showGridLines = False


def _count_codes_formula(sheet: str, row: int, columns: List[int], codes: List[str], weights: Dict[str, int] | None = None) -> str:
    terms = []
    safe = sheet.replace("'", "''")
    for c1, c2 in _contiguous_runs(columns):
        a1, a2 = get_column_letter(c1), get_column_letter(c2)
        for code in codes:
            base = f'COUNTIF(\'{safe}\'!{a1}{row}:{a2}{row},"{code}")'
            weight = 1 if weights is None else int(weights.get(code, 1))
            terms.append(f"({base}*{weight})" if weight != 1 else base)
    return "=" + "+".join(terms) if terms else "=0"


def _write_rotatorio_ndf(ws, spec: CalendarSpec, dates: List[date], year: int, layout: dict) -> None:
    count = len(spec.people)
    start_row = 5 + count + 1  # una fila en blanco tras el último operador
    cal_start = int(layout["cal_start"])
    months = _accounting_months(dates, year)
    month_cols = {m: [] for m in range(1, 13)}
    for i, m in enumerate(months):
        if m:
            month_cols[m].append(cal_start + i)

    # Limpieza de la zona izquierda inferior.
    for r in range(start_row, max(ws.max_row, start_row + 4 * (count + 4)) + 1):
        for c in range(1, 11):
            ws.cell(r, c).value = None

    month_fill = PatternFill("solid", fgColor="FFD966")
    month_fill2 = PatternFill("solid", fgColor="9DC3E6")
    row_fill_odd = PatternFill("solid", fgColor="FFF2CC")
    row_fill_even = PatternFill("solid", fgColor="D9D9D9")
    thin = Side(style="thin", color="000000")
    medium = Side(style="medium", color="000000")

    def ndf_border(col: int, *, first_row: bool = False, last_row: bool = False) -> Border:
        """Bordes del bloque N/D/F, independientes de la posición en plantilla."""
        if col == 1:
            left = medium
            right = Side(style=None)
        else:
            left = medium if col in (2, 5, 8) else thin
            right = medium if col in (4, 7, 10) else thin
        return Border(
            left=left,
            right=right,
            top=medium if first_row else thin,
            bottom=medium if last_row else thin,
        )

    def month_header_border(col: int) -> Border:
        return Border(
            left=medium if col in (2, 5, 8) else thin,
            right=medium if col in (4, 7, 10) else thin,
            top=medium,
            bottom=medium,
        )
    weights_n = {"N": 7, "ND": 7, "NF": 7, "T": 1, "TD": 1, "TF": 1}
    d_codes = ["MD", "TD", "ND", "RD"]
    f_codes = ["MF", "TF", "NF", "RF"]
    # Turnos creados en Rotatorio: X -> N/T/M/R. Sus sufijos D/F también
    # participan en los conteos con la misma semántica que el turno padre.
    aliases = {str(k).upper(): str(v).upper() for k, v in dict(spec.settings.get("shift_aliases", {})).items()}
    def family(code):
        cur = code; seen = set()
        while cur in aliases and cur not in seen:
            seen.add(cur); cur = aliases[cur]
        return cur
    for code in aliases:
        fam = family(code)
        if fam == "N":
            weights_n[code] = 7; weights_n[code + "D"] = 7; weights_n[code + "F"] = 7
            d_codes.append(code + "D"); f_codes.append(code + "F")
        elif fam == "T":
            weights_n[code] = 1; weights_n[code + "D"] = 1; weights_n[code + "F"] = 1
            d_codes.append(code + "D"); f_codes.append(code + "F")
        elif fam in {"M", "M1"}:
            d_codes.append(code + "D"); f_codes.append(code + "F")
        elif fam == "R":
            f_codes.append(code + "F")
    source_sheet = layout["sheet"]

    for block in range(4):
        top = start_row + block * (count + 4)
        months_block = [block * 3 + 1, block * 3 + 2, block * 3 + 3]

        # Las dos filas de separación anteriores a cada bloque (salvo el
        # primero, cuya separación ya se limpia en _prepare_operator_area)
        # también deben quedar sin estilos heredados.
        if block > 0:
            for blank_row in (top - 2, top - 1):
                for c in range(1, 11):
                    ws.cell(blank_row, c)._style = None

        for j, m in enumerate(months_block):
            c = 2 + j * 3
            ws.merge_cells(start_row=top, start_column=c, end_row=top, end_column=c + 2)
            ws.cell(top, c).value = MONTHS_TITLE[m - 1]
            ws.cell(top, c).fill = copy(month_fill if j % 2 == 0 else month_fill2)
            ws.cell(top, c).font = Font(name="Calibri", size=11, bold=True)
            ws.cell(top, c).alignment = Alignment(horizontal="center")
            ws.cell(top, c).border = Border(left=medium, right=medium, top=medium, bottom=medium)
            for k, code in enumerate(("N", "D", "F")):
                cell = ws.cell(top + 1, c + k)
                cell.value = code
                cell.fill = copy(month_fill if j % 2 == 0 else month_fill2)
                cell.font = Font(name="Calibri", size=11, bold=True)
                cell.alignment = Alignment(horizontal="center")
                cell.border = month_header_border(c + k)
        for idx, p in enumerate(spec.people):
            out_row = top + 2 + idx
            source_row = 5 + idx
            data_fill = row_fill_odd if idx % 2 == 0 else row_fill_even
            name_cell = ws.cell(out_row, 1)
            name_cell.value = p.name
            name_cell.fill = copy(data_fill)
            name_cell.font = Font(name="Calibri", size=11, bold=True)
            name_cell.alignment = Alignment(horizontal="center", vertical="center")
            name_cell.border = ndf_border(1, first_row=idx == 0, last_row=idx == count - 1)
            for j, m in enumerate(months_block):
                c = 2 + j * 3
                ws.cell(out_row, c).value = _count_codes_formula(source_sheet, source_row, month_cols[m], list(weights_n), weights_n)
                ws.cell(out_row, c + 1).value = _count_codes_formula(source_sheet, source_row, month_cols[m], d_codes)
                ws.cell(out_row, c + 2).value = _count_codes_formula(source_sheet, source_row, month_cols[m], f_codes)
                for k in range(3):
                    cell = ws.cell(out_row, c + k)
                    cell.fill = copy(data_fill)
                    cell.font = Font(name="Calibri", size=11, bold=True)
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                    cell.border = ndf_border(
                        c + k,
                        first_row=idx == 0,
                        last_row=idx == count - 1,
                    )


def generate_excel(
    spec: CalendarSpec,
    schedule: Schedule,
    holidays: Dict[date, HolidayInfo],
    year: int,
    community: str,
    city: str,
    output_path: Path,
) -> Path:
    layout = OUTPUT_LAYOUTS[spec.key]
    template = type_template_file(spec.key)
    wb = load_workbook(template)
    wb.calculation = CalcProperties(calcMode="auto", fullCalcOnLoad=True, forceFullCalc=True, calcOnSave=True)
    for name in list(wb.defined_names.keys()):
        item = wb.defined_names[name]
        if "#REF!" in str(getattr(item, "attr_text", "")):
            del wb.defined_names[name]

    sheet_name = layout["sheet"]
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"La plantilla tipo de {spec.title} no contiene la hoja {sheet_name!r}.")
    ws = wb[sheet_name]
    ws.conditional_formatting = ConditionalFormattingList()
    dates = calendar_dates(year)
    if layout.get("grouped") or spec.key == "Rotatorio":
        # Las plantillas de estos tipos muestran el año en A1.
        if spec.key != "Rotatorio" or ws["A1"].value is not None:
            ws["A1"] = year

    _write_headers(ws, dates, holidays, int(layout["cal_start"]))
    _prepare_operator_area(ws, spec, layout, dates)
    _write_people(ws, spec, schedule, year, dates, layout)
    if spec.key == "Rotatorio":
        _restore_rotatorio_vacation_merges(ws, spec)
    _write_holidays(wb, year, community, holidays)
    install_legend(wb, spec.key == "Rotatorio")
    _write_tt_conteo(wb, spec, schedule, dates, year)
    if spec.key == "Rotatorio":
        _write_rotatorio_ndf(ws, spec, dates, year, layout)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return output_path
