# Análisis de ajustes v2.7.3

## Objetivo
Endurecer la validación de los comienzos configurables incorporados en v2.7.2 para que una entrada manual extraña o una combinación incompatible nunca se ignore silenciosamente.

## Cambios realizados
- Se elimina el `fallback` genérico ante cualquier `TemplateValidationError`. La compatibilidad hacia atrás se activa únicamente cuando falta realmente la columna nueva.
- La lectura de fases solo admite formatos conocidos del desplegable.
- Los desplegables rosas usan validación Excel de tipo `Stop`, con mensaje de error y opción de dejar la celda vacía.
- Se valida la coherencia entre inicio TT, patrón TT y estado de Teletrabajo.
- Se añade defensa adicional en `scheduler.py` por si se construye un `CalendarSpec` fuera del lector de Excel.

## Reglas resultantes
- Intensivo: la persona inicial debe existir, estar activa y tener TT habilitado (`Sí` o `Renuncia`).
- Rotatorio: la fase debe pertenecer al ciclo y las fases elegidas deben respetar el máximo de Refuerzos.
- EasyVista/Puesto Usuario: Inicio TT válido, dentro del ciclo, TT habilitado y capacidad semanal respetada.
- Farmacia: la persona del primer sábado debe existir y estar activa.
- Sistemas: Inicio ciclo TT solo para `2 presenciales + 1 TT`, con TT habilitado; los MA no pueden coincidir en su semana TT.
- Supervisores: Orden TT solo con TT habilitado, dentro del ciclo y respetando el máximo del subgrupo.

## Validación
- 59/59 pruebas automatizadas correctas.
- Se incluyen pruebas específicas de texto manual inválido, TT deshabilitado y patrones incompatibles.
