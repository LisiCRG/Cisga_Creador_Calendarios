# Validación v2.8.1

## Pruebas automatizadas

Resultado: **66/66 tests correctos**.

Incluyen, además de la lógica acumulada de versiones anteriores:

- sufijo `_E01` verificado para los siete nombres de salida;
- Rotatorio: fila separadora sin valores, rellenos ni bordes;
- Rotatorio: primera fila N/D/F con formato amarillo y alternancia amarillo/gris independiente de la posición;
- carga de la plantilla oficial v13;
- listas de Turno base v2.7.4 comprobadas por departamento;
- Intensivo: `M/M1/M2`; EasyVista/Puesto: `M/MA/M2`; Sistemas: `M/MA/M1/M2`;
- Rotatorio sin `M1/M2` estándar y Farmacia sin `F3`;
- ausencia de validaciones antiguas solapadas en los rangos corregidos;
- rechazo de texto manual no válido en Inicio ciclo / Inicio TT / Orden TT;
- ausencia de fallback silencioso a plantilla antigua;
- Intensivo: inicio de cinta incompatible con `Teletrabajo=No`;
- EasyVista/Puesto Usuario: Inicio TT incompatible con `Teletrabajo=No`;
- Sistemas: Inicio ciclo TT solo para `2 presenciales + 1 TT`;
- Supervisores: Orden TT incompatible con `Teletrabajo=No`;
- Farmacia: persona inicial inexistente/inactiva;
- validaciones Excel rosas con estilo `Stop` y celda vacía permitida;
- M2, turnos creados, festivos, conteos y reglas anteriores.

## Integración

Se cargan y generan correctamente los siete calendarios para 2027 usando `Plantilla_Cuadrantes_Usuarios_v13.xlsx`.

## Validación v2.7.2

- 46/46 pruebas automatizadas correctas.
- Carga de plantilla v11 correcta.
- Siete calendarios generados para 2027.
- Intensivo: selector de primera TT comprobado.
- Rotatorio: 12 fases explícitas comprobadas con máximo 2 R.
- EasyVista/Puesto: TT semana 1/2/3 comprobado.
- Farmacia: primer sábado configurable comprobado.
- Sistemas: tres posiciones del ciclo TT comprobadas.
- Supervisores: orden TT por subgrupo comprobado; Marian mantiene TT visible en la fase seleccionada.



## v2.7.8

- 73/73 pruebas correctas ejecutadas por bloques.
- Regresión específica para formatos fantasma del General.
- Validación de Leyenda única y Festivos único; General sin Organización ni Conteo desde v2.8.3.


## v2.8.0

- Casillas GUI 24/12 y 31/12 desmarcadas por defecto.
- Festivo opcional aplicado como descanso en calendarios no rotatorios y como turno festivo en Rotatorio.
- Fechas seleccionadas incluidas en `Festivos [año]`.
- Aplicación a años adyacentes visibles para semanas de borde.
- Suite completa: **77/77 pruebas correctas**, ejecutada por bloques.
