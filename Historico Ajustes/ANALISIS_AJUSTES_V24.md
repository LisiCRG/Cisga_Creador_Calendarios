# Análisis de ajustes v2.4

## Motivo del cambio

El cuadrante real de Intensivo muestra una geometría más simple que el algoritmo A/B anterior: cada semana existe el mismo bloque vertical de 18 posiciones y el bloque se desplaza una fila.

La semana del 14/12/2026 reproduce exactamente:

```text
TT, P, TT, TT, M, M, M, M, M, TT, P, TT, M, M, M, M, M, M
```

La semana siguiente aparece la misma cinta desplazada una fila hacia abajo.

## Consecuencias

- Siempre existen 5 posiciones TT teóricas por semana.
- Existen 2 posiciones P teóricas.
- Cada persona recorre las 18 posiciones en 18 semanas.
- Las dos P están separadas 9 posiciones, por lo que una persona M tiene una P cada 9 semanas.
- M1 elimina únicamente la P que le cae a esa persona; no desplaza ni altera la cinta.
- Una Renuncia a TT conserva la posición y cuenta dentro del máximo semanal.

## Ventaja técnica

Se elimina la búsqueda/optimización de fases para Intensivo. El calendario queda determinado por tres elementos visibles para el usuario:

1. orden de personas;
2. cinta de la plantilla;
3. semana ancla.

Esto reproduce mejor el cuadrante real y hace la regla más fácil de mantener.
