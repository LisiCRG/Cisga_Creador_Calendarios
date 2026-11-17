# Análisis de ajustes v2.3

## Intensivo

El bloqueo de capacidad se debía al valor `Máximo TT = 4`. El patrón A/B consume 5 plazas TT por persona cada 18 semanas. Con 18 personas TT activas:

```text
18 × 5 = 90 plazas TT
18 semanas × 5 = 90 plazas disponibles
```

Por tanto, **5 es el máximo/coincidencia semanal coherente con el patrón y la plantilla actual**. La plantilla v6 queda configurada en 5.

Ángeles, Vanesa y Carlos siguen en M1 y no participan en P. Ángeles mantiene Renuncia a TT y su plaza cuenta dentro de las 5.

## Rotatorio

Se mantienen 12 personas activas: Daniel Ameijeiras está documentado pero `Activo=No`, y Saraid entra activa. La fila inmediatamente posterior al último agente se deja visible y vacía antes del resumen N/D/F. Las combinaciones B:D, E:G y H:J se restauran después de escribir.

## Cabeceras/subdepartamentos

EasyVista, Puesto Usuario, Sistemas Áreas Especializadas y Supervisores/OPX heredaban el texto de grupo con rotación de 90 grados. v2.3 lo deja en orientación horizontal (`0°`) y asegura un ancho mínimo de columna para lectura normal.

## Integración por departamento

- **Intensivo**: validación de P, TT, M1 y Renuncia integrada; max TT=5 ya es viable.
- **Rotatorio**: activo/inactivo, ciclo, R, TT, N/D/F, combinaciones y separación visual integrados.
- **EasyVista**: TT 2+1, festivos y grupo horizontal integrados.
- **Puesto Usuario**: misma lógica 2+1 y grupo horizontal integrados.
- **Farmacia**: F1/F2 y sábados alternos; no usa TT; sigue protegida contra celdas combinadas heredadas.
- **Sistemas**: patrones TT y separación MA; grupos horizontales.
- **Supervisores**: límites TT por grupo, Renuncia, M1, Guardia y grupos horizontales.

Los siete calendarios se han generado como prueba de integración sin error de celdas combinadas.
