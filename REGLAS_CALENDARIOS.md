# Reglas de calendarios v2.8.1

## Regla común de turnos creados

Un código creado puede heredar el comportamiento de un turno existente mediante `TURNOS DISPONIBLES / CREADOS`. El código visible se conserva, pero la planificación utiliza la familia heredada.

M2 se entrega por defecto como M2 → M1.

## Intensivo

- Cinta: `TT,P,TT,TT,M,M,M,M,M,TT,P,TT,M,M,M,M,M,M`.
- Máximo 5 TT y 2 P por semana.
- M1/M2 y cualquier alias que resuelva a M1 no hacen P.
- Fines de semana y festivos nacionales/CyL: D.

## Rotatorio

- Ciclo por días editable.
- N inicia miércoles.
- R L-V y máximo configurable.
- Trabaja fines de semana y festivos.
- Sufijos D/F.
- M/M1/R con TT en L-V no festivo.
- N/D/F por mes de la semana más nueva.
- Turnos creados heredan familia para R, TT, sufijos y conteos.

## EasyVista / Puesto Usuario

- Fines de semana y festivos nacionales/CyL: D.
- Ciclo semanal editable por turno base.
- TT mantiene el código visible y aplica borde.
- Un turno creado puede heredar el ciclo del padre o tener una fila propia.

## Farmacia

- Dos posiciones funcionales equivalentes a F1 y F2.
- Sábados alternos.
- Domingo y festivos nacionales/CyL: D.
- Un alias puede reemplazar visualmente F1/F2.

## Sistemas

- Fines de semana/festivos nacionales/CyL: D.
- Patrón TT por persona.
- Familia MA mantiene la regla de no coincidencia en TT.
- Turnos creados heredan familia.

## Supervisores

- Fines de semana/festivos nacionales/CyL: D salvo Guardia.
- G trabaja L-D y prevalece.
- Ciclo TT editable.
- Máximo TT por grupo.
- Turnos creados mantienen el ciclo TT del turno base.

## Inicio configurable v2.7.2

Las reglas de los turnos no cambian. La plantilla permite elegir la posición inicial de cada rotación. El orden de filas sigue siendo el orden de salida y los subdepartamentos/grupos se conservan.

## Validación de inicios v2.7.4

- Los valores de inicio solo admiten opciones conocidas del desplegable o vacío.
- Vacío mantiene el reparto automático/continuidad histórica.
- `Teletrabajo=No` es incompatible con Inicio TT/Orden TT.
- Sistemas solo admite Inicio ciclo TT para `2 presenciales + 1 TT`.
- Las incompatibilidades globales (máximos R/TT, coincidencias MA, límites de subgrupo) siguen comprobándose al construir el calendario.
