# Análisis de ajustes v2.7.2

## Objetivo
Permitir que el usuario decida **cómo comienza cada rotación al inicio del año** sin modificar la lógica de los turnos.

## Diseño
Las celdas rosa pastel son selectores de fase. El verde sigue siendo regla/ciclo editable y el azul datos de personas.

### Intensivo
Se selecciona la persona que ocupa la primera `TT` de la cinta en la Semana 1. La cinta conserva su orden y baja una fila cada semana.

### Rotatorio
Cada agente puede elegir una de 12 fases semanales válidas. Son desplazamientos de 7 días sobre el ciclo de 84 días, por lo que las Noches continúan empezando en miércoles y los Refuerzos siguen de lunes a viernes.

### EasyVista / Puesto Usuario
Cada persona selecciona si su primer TT del año cae en la semana 1, 2 o 3. El resto del ciclo continúa automáticamente.

### Farmacia
Se selecciona quién trabaja el primer sábado del año; el segundo sábado corresponde al otro turno y continúa alternando.

### Sistemas Áreas Especializadas
Las personas con patrón `2 presenciales + 1 TT` pueden empezar en primera presencial, segunda presencial o TT. Los MA siguen sin poder coincidir en TT.

### Supervisores
Se define el orden TT 1/2/3 dentro de cada subgrupo. La Guardia continúa teniendo prioridad si coincide.

## Compatibilidad
Si no se informa una fase, se conserva el reparto automático de versiones anteriores. Los turnos creados y alias (`M2 → M1`, etc.) siguen funcionando.
