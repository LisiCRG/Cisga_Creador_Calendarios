# Manual de la plantilla de configuración · v2.8.1

Plantilla oficial: `Plantilla_Cuadrantes_Usuarios_v13.xlsx`.

## Pestañas

- `INICIO`
- `INSTRUCCIONES`
- `Intensivo`
- `Rotatorio`
- `EasyVista`
- `Puesto Usuario`
- `Farmacia`
- `Sistemas`
- `Supervisores`

`INSTRUCCIONES` es una guía de usuario. No contiene datos obligatorios para validar.

## Datos de personas

Las filas azules contienen datos modificables: nombre, grupo, turno base, Teletrabajo y Activo según el departamento.

`Activo=No` excluye a la persona de la generación sin obligar a borrar la fila.

Teletrabajo admite:

- `Sí`: borde amarillo cuando corresponda.
- `Renuncia`: borde magenta y sigue contando como plaza TT.
- `No`: fuera del TT.

## Turnos disponibles / creados

Cada departamento incluye una tabla verde:

```text
Código | Se comporta como | Descripción
```

Los códigos nativos pueden aparecer con `Se comporta como` vacío. Los códigos nuevos deben indicar de qué turno heredan las reglas.

Ejemplo incluido:

```text
M2 | M1 | Mañana 2
```

El motor resuelve cadenas de herencia. En departamentos donde M1 se comporta como M, M2 puede encadenarse como M2 → M1 → M.

## Crear un código

1. Use la primera fila verde libre de la tabla.
2. Escriba un código único.
3. Indique `Se comporta como`.
4. Seleccione/escriba el código en la persona o ciclo correspondiente.
5. Valide la plantilla.

## Ciclos

- Intensivo: cinta circular.
- Rotatorio: bloques por días.
- EasyVista/Puesto Usuario: ciclo por semanas.
- Farmacia: alternancia de sábado.
- Sistemas: patrón TT por persona.
- Supervisores: ciclo TT, límites por grupo y Guardia.

## Turnos base estándar v2.7.4

- Intensivo: `M`, `M1`, `M2`.
- Rotatorio: no usa `M1` ni `M2` como turnos estándar.
- EasyVista: `M`, `MA`, `M2`.
- Puesto Usuario: `M`, `MA`, `M2`.
- Farmacia: únicamente `F1`, `F2`.
- Sistemas: `M`, `MA`, `M1`, `M2`.

## M2

M2 está incluido de fábrica. En Intensivo hereda M1, por lo que no hace Partido. En el resto mantiene las reglas de M1/M según el departamento.


## Corrección 2.7.1 · Intensivo

El desplegable **Turno base** toma los códigos de la tabla verde `TURNOS DISPONIBLES / CREADOS`. De serie ofrece `M`, `M1` y `M2`. `M2` se comporta como `M1`, por lo que no realiza Partido. Si se añade un código nuevo en las filas verdes disponibles, queda disponible para selección en el mismo desplegable.

## Celdas ROSA · cómo empieza el año

El rosa no cambia las reglas del calendario. Solo fija la **fase inicial**.

| Calendario | Selector rosa | Ejemplo |
|---|---|---|
| Intensivo | Inicio cinta · 1ª posición TT | Marcos inicia la primera TT de Semana 1 |
| Rotatorio | Inicio ciclo F01..F12 | F03 = Ciclo 1 · Mañana 1 |
| EasyVista / Puesto | Inicio TT | TT semana 1 / 2 / 3 |
| Farmacia | Primer sábado | Sofía o Judit |
| Sistemas | Inicio ciclo TT | 1ª sin TT / 2ª sin TT / Semana TT |
| Supervisores | Orden TT | TT semana 1 / 2 / 3 dentro del subgrupo |

En Rotatorio las 12 fases son las únicas fases semanales válidas del ciclo de 84 días; por eso conservan la alineación de Noche y Refuerzo.

