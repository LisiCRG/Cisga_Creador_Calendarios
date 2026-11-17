# GENERADOR DE CUADRANTES v2.8.1

## Corrección v2.8.1 · Festivos locales

- Los festivos locales generan `D` en todos los calendarios no rotatorios.
- Rotatorio los trata como festivos de trabajo (`MF`, `TF`, `NF`, `RF`, etc.).
- En Supervisores, un festivo prevalece sobre la guardia (`G`) y se muestra `D`.
- No hay cambios adicionales de formato, estructura ni reglas.


## Novedad v2.8.0 · General CAU unificado y festivos opcionales en ocre

- **24/12** y **31/12** siguen siendo opcionales desde la GUI. Si se marcan, su cabecera se muestra en ocre `#BF8F00`.
- En departamentos no rotatorios se descansan como `D`; Rotatorio mantiene su semántica de festivo con sufijo `F`.
- Los Excel individuales siguen generándose igual y conservan `_E01`.
- El General CAU mantiene el nombre `Calendario_General_CAU_[año]_E01.xlsx`, pero sus calendarios se concentran en una única hoja **General**.
- Estructura normalizada de cada bloque: **Subdepartamento | Operador | días**.
- El General no incluye columnas de vacaciones ni el resumen N/D/F de Rotatorio.
- Cada departamento tiene una fila roja en negrita y una separación visual antes del siguiente.
- Intensivo, Rotatorio y Farmacia reciben una columna de subdepartamento con su propio nombre para alinear todos los bloques.
- Se mantienen una única **Leyenda**, **Organización** y **Festivos [año]**.

Aplicación Windows/Python para generar calendarios SACYL a partir de una **plantilla Excel editable por usuarios**.

## Corrección v2.7.5 · Nombres E01 y formato Rotatorio

- Todos los Excel generados terminan en `_E01` (por ejemplo, `Calendario_Rotatorio_2027_E01.xlsx`).
- Rotatorio deja completamente sin formato la fila separadora entre el último agente y el resumen N/D/F.
- El resumen N/D/F aplica su formato de forma explícita y dinámica, sin depender de la fila original de la plantilla.
- Francisco Javier Gutierrez, como primera fila del resumen, conserva siempre el formato amarillo correspondiente.
- Las filas siguientes alternan amarillo/gris correctamente en los cuatro bloques trimestrales.
- Suite de validación: **66/66 pruebas correctas**.

## Corrección v2.7.4 · Turnos base por departamento

- Los campos rosas de inicio bloquean valores que no estén en el desplegable.
- Dejarlos vacíos sigue siendo válido y conserva el modo automático/histórico.
- El lector ya no confunde un valor inválido con una plantilla antigua.
- Se rechazan combinaciones sin sentido, como asignar Inicio TT a una persona con `Teletrabajo=No` o configurar Inicio ciclo TT en Sistemas para `Siempre TT`.
- La plantilla oficial pasa a `Plantilla_Cuadrantes_Usuarios_v13.xlsx`.
- Intensivo: `Turno base = M / M1 / M2`.
- Rotatorio: la plantilla estándar no incluye `M1` ni `M2`.
- EasyVista y Puesto Usuario: `Turno base = M / MA / M2`.
- Farmacia: solo `F1 / F2`; se elimina `F3` de la plantilla estándar.
- Sistemas: `Turno base = M / MA / M1 / M2`.
- Se han eliminado validaciones solapadas que podían mostrar listas antiguas en Excel.
- Suite de validación: **64/64 pruebas correctas**.


## Corrección v2.7.1

- El desplegable `Turno base` de Intensivo se alimenta de la tabla verde `TURNOS DISPONIBLES / CREADOS`.
- Incluye `M`, `M1` y `M2` de serie, y admite códigos nuevos añadidos en las filas verdes.
- `M2 → M1`: conserva el texto `M2`, hereda las reglas de `M1` y por tanto no realiza `P`.

## Novedades v2.7

- Plantilla oficial: `Plantilla_Cuadrantes_Usuarios_v13.xlsx`.
- Nueva pestaña `INSTRUCCIONES` con ejemplos visuales para cambiar reglas, ciclos y crear turnos.
- Nuevo turno `M2`, disponible en la plantilla y definido por defecto como **M2 → M1**.
- `M2` conserva su código visible, pero hereda las reglas funcionales de `M1`.
- En Intensivo, `M1` y `M2` no hacen `P`.
- Todos los departamentos incorporan una tabla verde `TURNOS DISPONIBLES / CREADOS`.
- Un turno nuevo puede heredar el comportamiento de otro sin modificar Python.
- EasyVista y Puesto Usuario siguen permitiendo definir además un ciclo semanal propio.
- Rotatorio permite usar turnos creados en su ciclo por días y hereda domingo/festivo/conteo N-D-F de su familia.
- Farmacia usa únicamente F1 y F2 en la plantilla estándar.
- Sistemas y Supervisores aceptan turnos creados como turno base.
- Los estilos Excel de un turno creado heredan el color de su turno padre.
- Se mantiene la corrección de PyInstaller para los catálogos de traducción de `python-holidays`.

## Flujo de trabajo

1. Seleccionar `Plantilla_Cuadrantes_Usuarios_v13.xlsx`.
2. Validar / cargar la plantilla.
3. Elegir año, comunidad, ciudad y festivos locales.
4. Marcar los calendarios a generar.
5. Elegir carpeta de salida.
6. Generar los calendarios en el orden de la plantilla.

La GUI incluye **Generar plantilla tipo…** y **Ayuda para editar turnos**.

## Cómo crear un turno nuevo

Cada pestaña de departamento contiene al final una tabla verde:

```text
TURNOS DISPONIBLES / CREADOS
Código | Se comporta como | Descripción
```

Ejemplo:

```text
M2 | M1 | Mañana 2
```

`M2` se verá como `M2` en el calendario, pero el motor aplicará las reglas de `M1`.

Para crear otro turno, use la primera fila verde libre y escriba el nuevo código y el turno del que hereda las reglas. Después utilice ese código en `Turno base`, `Turno` o en el ciclo editable correspondiente.

## Intensivo

Cinta circular actual:

```text
TT,P,TT,TT,M,M,M,M,M,TT,P,TT,M,M,M,M,M,M
```

Reglas principales:

- 5 posiciones TT por semana.
- Hasta 2 P por semana.
- La cinta baja una fila por semana y continúa entre años.
- M1 y M2 no hacen P.
- Ángeles, Vanesa y Carlos siguen configurados como M1.
- Ángeles tiene `Renuncia` a TT: borde magenta y cuenta dentro del límite TT.
- Los turnos creados que se comporten como M1 tampoco hacen P.

## Rotatorio

Se mantiene la lógica validada:

- ciclo por días editable;
- N inicia en miércoles;
- R de lunes a viernes;
- domingos y festivos con sufijos D/F;
- M/M1 y R son TT en L-V no festivo según `Sí/Renuncia/No`;
- N/D/F se imputa al mes más nuevo cuando una semana cruza dos meses;
- B:D, E:G y H:J permanecen agrupadas;
- fila en blanco antes del bloque N/D/F;
- 12 personas activas: Daniel Ameijeiras inactivo y Saraid Lozada activa.

Un turno creado en Rotatorio hereda las reglas del turno padre. Ejemplo:

```text
N2 → N
```

y puede utilizarse en el ciclo como `N2 × 7`.

## EasyVista y Puesto Usuario

El bloque `CICLO POR SEMANAS` sigue siendo editable. Ejemplo:

```text
M | M | M | TT
```

puede convertirse en:

```text
M | TT | TT | TT
```

siempre revisando `Máximo TT por semana`.

Los turnos creados pueden heredar el ciclo de otro turno o disponer de una fila de ciclo propia.

## Farmacia

Mantiene dos posiciones funcionales F1/F2 y sábados alternos. La plantilla estándar solo ofrece F1 y F2; no incorpora F3.

## Sistemas Áreas Especializadas

Los turnos base pueden ser creados. El patrón TT de cada persona sigue determinando `Siempre TT` o `2 presenciales + 1 TT`. Los turnos que hereden MA conservan la regla de no coincidencia de MA en TT.

## Supervisores y OPX

Se mantienen:

- ciclo TT editable;
- máximos TT por grupo;
- Guardia semanal;
- Guardia prevalece sobre TT;
- reparto TT evita, cuando es posible, que la fase TT de una persona coincida siempre con su Guardia.

`M2` está disponible y hereda `M1`.

## Convención visual de la plantilla

- **Verde pastel:** regla, ciclo o definición de turno editable.
- **Azul claro:** datos de personas.
- **Blanco/gris:** información o reglas descriptivas.

Consulte la pestaña `INSTRUCCIONES`, `MANUAL_PLANTILLA.md` e `INSTRUCCIONES_TURNOS.md`.

## Desarrollo y compilación

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm GENERADOR_TURNOS.spec
```

## Novedad v2.7.2 · Inicio de ciclos configurable

La plantilla v13 mantiene celdas **rosa pastel** para decidir cómo comienza el año sin cambiar la regla del turno:

- **Intensivo**: persona que ocupa la primera posición TT de la cinta en la Semana 1.
- **Rotatorio**: fase F01..F12 por agente, manteniendo Noches en miércoles y Refuerzo de lunes a viernes.
- **EasyVista / Puesto Usuario**: semana 1, 2 o 3 en la que cada persona realiza su primer TT.
- **Farmacia**: persona que trabaja el primer sábado del año.
- **Sistemas**: inicio del ciclo `2 presenciales + 1 TT`.
- **Supervisores**: orden TT 1/2/3 por subgrupo.

Si una celda rosa se deja vacía, el motor conserva el comportamiento automático/histórico compatible con versiones anteriores cuando sea posible.
