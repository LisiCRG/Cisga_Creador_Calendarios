# Análisis de ajustes v2.6

## Error solo al compilar

El error `No translation file found for domain: 'ES'` no estaba provocado por la plantilla. Se producía al ejecutar el EXE porque `python-holidays` usa catálogos gettext para traducir los nombres de festivos y el `.spec` v2.5 incluía el módulo Python, pero no todos sus ficheros de datos.

La v2.6 lo corrige por dos vías:

1. `GENERADOR_TURNOS.spec` usa `collect_all("holidays")`, que añade datos, binarios y submódulos del paquete al ejecutable.
2. `_spain_calendar()` intenta español y, ante un error de catálogo, reintenta sin idioma forzado.

El segundo punto es una protección adicional; con el `.spec` nuevo no debería ser necesario activar el fallback.

## Plantilla v9

El verde anterior `#E2F0D9` era demasiado tenue en algunos monitores. Las reglas y ciclos editables relevantes pasan a `#C6E0B4`, con texto verde oscuro, manteniendo azul claro para datos de personas/opciones.

No se modifica ninguna regla de planificación ni la salida de los siete departamentos.
