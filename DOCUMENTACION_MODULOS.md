# Documentación de módulos — GENERADOR DE CUADRANTES v2.8.1

## `main.py`
Punto de entrada de la aplicación.

## `src/turnos/gui.py`
Interfaz Tkinter. Selecciona plantilla, año, festivos, calendarios y carpeta. Exporta la plantilla v10 y muestra ayuda resumida de creación de turnos.

## `src/turnos/template_reader.py`
Convierte la plantilla Excel en `CalendarSpec`.

Novedades v2.7:

- lee `TURNOS DISPONIBLES / CREADOS`;
- construye `shift_aliases` (`M2 → M1`, `N2 → N`, etc.);
- Intensivo usa `Turno base` explícito en lugar de inferir solo reducción;
- EasyVista/Puesto Usuario permiten que un turno creado herede el ciclo del padre;
- añade automáticamente turnos creados a la leyenda si faltan.

## `src/turnos/scheduler.py`
Motor de planificación.

Novedades v2.7:

- `shift_family()` resuelve el comportamiento heredado;
- M2/alias de M1 no hacen P en Intensivo;
- Rotatorio usa familia heredada para R, TT, domingo/festivo;
- Farmacia acepta alias funcionales de F1/F2;
- Sistemas reconoce alias MA para la no coincidencia TT;
- Supervisores conserva el código creado y aplica su ciclo TT.

## `src/turnos/excel_generator.py`
Genera los Excel finales. Los turnos creados heredan el estilo visual de su padre. Rotatorio amplía N/D/F con códigos creados de familia N/T/M/R.

## `src/turnos/holidays_provider.py`
Festivos nacionales/autonómicos con `python-holidays` y locales persistentes. Mantiene fallback de idioma para el EXE.

## `src/turnos/paths.py`
Rutas de recursos. Plantilla oficial: `templates/Plantilla_Cuadrantes_Usuarios_v13.xlsx`.

## `src/turnos/models.py`
Dataclasses del dominio: personas, calendarios, festivos, leyenda y plantilla.

## `src/turnos/catalog.py`
Orden, nombres visibles y nombres de archivos de salida.

## Tests
`tests/` cubre calendario, plantilla, reglas históricas, MergedCell, PyInstaller y creación/herencia de turnos v2.7.

## Cambios de arquitectura v2.7.2

`PersonSpec` incorpora `start_phase`, usado por Rotatorio, EasyVista/Puesto, Sistemas y Supervisores. Intensivo y Farmacia guardan el selector inicial en `CalendarSpec.settings`. `scheduler.py` aplica las fases explícitas y mantiene asignación automática como compatibilidad cuando no se informa una fase.

