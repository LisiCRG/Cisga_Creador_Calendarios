# Análisis de ajustes v2.7.5

## Objetivo

Dos correcciones de salida sin cambiar las reglas de planificación:

1. Añadir `_E01` al final de todos los nombres de Excel generados.
2. Hacer robusto el formato del resumen N/D/F de Rotatorio.

## Causa del formato de Rotatorio

El resumen N/D/F se desplaza verticalmente según el número de agentes activos. Parte del aspecto se estaba heredando de las filas que ocupaban esa posición en la plantilla tipo. Con 12 agentes, la primera fila del resumen caía sobre una antigua fila de cabecera, mientras que la fila separadora caía sobre una antigua fila de agente.

## Solución

- La fila separadora se limpia también a nivel de estilo, no solo de valores.
- Meses, cabeceras N/D/F y filas de personas reciben bordes, rellenos, fuente y alineación de forma explícita.
- Las filas de personas alternan amarillo `FFF2CC` y gris `D9D9D9`.
- El resultado ya no depende del número de agentes ni de la posición previa en la plantilla.

## Validación

- 66/66 pruebas automatizadas correctas.
- Generación Rotatorio 2027 comprobada visualmente.
- Sin errores de fórmula detectados en el Excel de prueba.
