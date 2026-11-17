# Análisis de ajustes v2.5

## Ciclos editables

La causa por la que cambiar `M | M | TT` a `TT | TT | TT` no tenía efecto en v2.4 era directa: la tabla de EasyVista/Puesto Usuario era visual, pero `scheduler.py` seguía usando un ciclo fijo de tres semanas (`Base · Base · TT`).

v2.5 lee el bloque `CICLO POR SEMANAS` desde la plantilla y construye el calendario con esos valores. También busca desfases entre personas para respetar `Máximo TT por semana`.

## Nuevos turnos

EasyVista/Puesto Usuario aceptan nuevas filas de turno base. El generador toma el código, el ciclo y lo aplica a cualquier persona que use ese Turno base. Los códigos nuevos reciben un estilo automático por familia y una leyenda genérica si no existía.

## Marian Gutiérrez

En v2.4, Supervisores tenía dos ciclos de 3 semanas con el mismo ancla:

- Guardia: Daniel → Marian → Adrián.
- TT por grupo: fase 0 → fase 1 → fase 2.

Marian había quedado asignada a fase TT 1, exactamente la misma fase en la que hacía Guardia. Como `G` prevalece, el TT quedaba oculto todas las veces y nunca aparecía borde amarillo.

v2.5 calcula el desfase TT minimizando las colisiones con Guardia antes de equilibrar el grupo. Con la plantilla oficial Marian conserva Guardia y también recibe semanas TT fuera de `G`.
