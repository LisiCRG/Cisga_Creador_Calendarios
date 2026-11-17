# Instrucciones para editar y crear turnos · v2.8.1

La plantilla v13 está pensada para que un usuario pueda hacer cambios sin tocar Python.

## 1. Colores

- Verde pastel: el programa lee ese parámetro o ciclo; puede modificarse.
- Azul claro: datos de personas.
- Blanco/gris: información orientativa.

## 2. Crear un turno nuevo

En cada departamento existe `TURNOS DISPONIBLES / CREADOS`.

Ejemplo:

```text
Código   Se comporta como   Descripción
M2       M1                 Mañana 2
```

`M2` conserva su nombre en el Excel generado, pero hereda las reglas de M1.

Para crear `X1` con reglas de M:

```text
X1       M                  Turno X de mañana
```

Después seleccione/escriba `X1` en `Turno base`, `Turno` o úselo en el ciclo del departamento.

## 3. M2

M2 está creado por defecto. En Intensivo se comporta como M1:

- no hace P;
- puede tener TT;
- `Sí` = borde amarillo;
- `Renuncia` = borde magenta y ocupa plaza TT;
- mantiene el código visible M2.

## 4. Ejemplos

### Intensivo

La cinta solo usa `M`, `P` y `TT`. Los turnos base de las personas pueden ser M, M1, M2 o un código creado que herede M/M1.

### Rotatorio

Para crear N2:

```text
N2 → N
```

Después cambie un bloque del ciclo a:

```text
N2 × 7
```

El motor lo tratará como N para inicio de noche, domingos, festivos y conteo N/D/F, pero se verá como N2/N2D/N2F.

### EasyVista / Puesto Usuario

Puede cambiar:

```text
M | M | M | TT
```

por:

```text
M | TT | TT | TT
```

Si crea M2 → M1 → M y no añade fila propia de ciclo, heredará el ciclo de M. Si quiere un patrón diferente, añada una fila M2 en `CICLO POR SEMANAS`.

### Farmacia

Ejemplo:

```text
FX → F1
```

Un código personalizado FX puede heredar F1 si se crea expresamente manteniendo su alternancia de sábados.

### Sistemas

Un turno nuevo hereda la familia M/MA indicada. El patrón TT configurado en la persona sigue mandando.

### Supervisores

Un turno nuevo conserva el ciclo TT del grupo. Guardia sigue prevaleciendo.

## 5. Validación

Si un cambio hace imposible respetar un máximo TT/P/R, el programa muestra un error. No aumenta límites ni mueve turnos de forma silenciosa.

## Rosa = fase inicial

Las celdas rosa pastel permiten ordenar el inicio del año. No crean un turno nuevo ni cambian su duración. Son independientes de las celdas verdes (reglas/ciclos) y azules (personas).

