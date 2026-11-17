# Análisis de ajustes v2.7

La v2.7 convierte la creación de turnos en una capacidad común a todos los departamentos.

## M2

Se incorpora M2 como código seleccionable. En Intensivo se define `M2 → M1`, por lo que nunca recibe P. Si le corresponde TT, conserva M2 con borde amarillo/magenta.

## Turnos creados

Cada departamento incluye una tabla verde. El motor lee `Código → Se comporta como` y usa la segunda columna como semántica funcional. Esto permite crear códigos sin recompilar.

## Casos soportados

- Intensivo: nuevos turnos de mañana que heredan M/M1.
- Rotatorio: turnos nuevos dentro del ciclo, incluidos sufijos D/F y conteo N/D/F por familia.
- EasyVista/Puesto Usuario: alias de ciclo o ciclo semanal propio.
- Farmacia: alias F1/F2.
- Sistemas: nuevos turnos M/MA.
- Supervisores: nuevos turnos base con el mismo ciclo TT y Guardia.

## Plantilla

Se añade `INSTRUCCIONES` y se mantiene el código de colores: verde para reglas/turnos editables y azul para personas.
