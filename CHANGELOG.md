## 2.8.2
- Corrección de numeración de semanas: las cabeceras usan ahora la semana ISO real de cada lunes.
- Se soportan años ISO con semana 53 sin asumir un máximo fijo de 52 semanas.
- El inicio visible de 2027 se muestra correctamente como `SEMANA 53` (lunes 28/12/2026), seguido de `SEMANA 1` el 04/01/2027.
- No se modifican las rotaciones ni las anclas históricas; el cambio afecta a la numeración visible de semanas.
- Añadidas pruebas de regresión para 2026→2027 y futuros años con semana 53.

## 2.8.1
- Corrección: los festivos locales generan `D` en todos los calendarios no rotatorios.
- Rotatorio aplica sufijo festivo (`MF`/`TF`/`NF`/`RF`...) también a los festivos locales.
- En Supervisores, un festivo prevalece sobre la guardia y se muestra `D`.

## 2.8.0

- 24/12 y 31/12 opcionales se muestran en ocre `#BF8F00` cuando están marcados como festivos.
- Calendarios no rotatorios: 24/12 y 31/12 marcados se tratan como `D`; Rotatorio conserva su lógica festiva `*F`.
- `Calendario_General_CAU_[año]_E01.xlsx` pasa a una única hoja de calendarios llamada `General`.
- Todos los departamentos se apilan verticalmente en `General`, con columnas normalizadas `Subdepartamento | Operador | días`.
- Se eliminan del General `DIAS VAC.`, `DISFRUTADOS` y `PENDIENTES`.
- El General no incluye el resumen mensual N/D/F de Rotatorio.
- Cada departamento incorpora una fila separadora roja en negrita y una fila en blanco entre bloques.
- Intensivo, Rotatorio y Farmacia reciben columna de subdepartamento propia para quedar alineados con el resto.
- Se mantienen una única `Leyenda`, `Organización` y `Festivos [año]`.
- Los Excel individuales no cambian salvo el nuevo color ocre de los festivos opcionales.

## 2.7.9

- Añadidas en la GUI inicial dos casillas independientes para tratar 24/12 y 31/12 como festivos.
- Desmarcadas por defecto: sin selección, el comportamiento se mantiene idéntico a v2.7.8.
- Al marcar una fecha, se incorpora al calendario de festivos y se aplica a todos los departamentos, incluidos los años adyacentes visibles en las semanas de borde.

## 2.7.8

- Eliminados formatos fantasma bajo los cuadrantes del General CAU.
- Los estilos de dimensión de filas/columnas ya no se copian entre workbooks; solo se conserva su geometría.
- General CAU con una única Leyenda deduplicada y ámbito por departamento.
- General CAU con una única hoja Organización.
- General CAU con una única hoja Festivos [año].

## 2.7.7

- Corregido el formato visual del Calendario General CAU.
- El libro General hereda el tema de Excel de los calendarios individuales.
- Los colores y fuentes basados en tema se muestran ahora exactamente igual que en cada fichero individual.
- Se conserva también la paleta de colores indexados por compatibilidad.
- Añadida prueba de regresión específica para el tema del General.

## 2.7.6

- Añade `Calendario_General_CAU_[año]_E01.xlsx` en cada generación con al menos un calendario correcto.
- El libro General incluye una pestaña por cada calendario individual generado en esa ejecución, conservando contenido, fórmulas y formato.
- Los Excel individuales se siguen generando sin cambios y mantienen el sufijo `_E01`.
- Suite de validación: **69/69 pruebas correctas**.

# Changelog

## 2.7.5
- Todos los ficheros de salida añaden el sufijo `_E01` antes de `.xlsx`.
- Rotatorio: la fila separadora bajo el último agente queda totalmente limpia de rellenos y bordes.
- Rotatorio: el bloque N/D/F aplica formato propio y dinámico, evitando herencias de estilos de filas antiguas de la plantilla.
- La primera persona del bloque N/D/F (Francisco Javier Gutierrez en la plantilla actual) recupera siempre el formato correcto.
- Alternancia amarillo/gris fijada para todas las filas del resumen N/D/F.
- 66 pruebas automatizadas correctas.

## 2.7.4
- Plantilla oficial `Plantilla_Cuadrantes_Usuarios_v13.xlsx`.
- Intensivo: Turno base ofrece exactamente `M`, `M1`, `M2`.
- Rotatorio: se eliminan `M1` y `M2` de los turnos estándar de la plantilla.
- EasyVista y Puesto Usuario: Turno base añade `M2` (`M`, `MA`, `M2`).
- Farmacia: la plantilla estándar contiene únicamente `F1` y `F2`; se elimina el ejemplo `F3`.
- Sistemas: Turno base ofrece `M`, `MA`, `M1`, `M2`.
- Se actualizan instrucciones y pruebas de regresión para fijar estas listas por departamento.
- 64 pruebas automatizadas correctas.


## 2.7.3
- Nueva plantilla `Plantilla_Cuadrantes_Usuarios_v12.xlsx`.
- Los selectores rosas de inicio usan validación Excel estricta (`Stop`) y permiten vacío para conservar el modo automático.
- Un valor manual no reconocido ya no activa silenciosamente la compatibilidad con plantillas antiguas: ahora produce un error de validación.
- EasyVista, Puesto Usuario y Supervisores rechazan un Inicio/Orden TT cuando `Teletrabajo=No`.
- Intensivo rechaza como inicio de la primera TT a una persona con `Teletrabajo=No`.
- Sistemas solo permite `Inicio ciclo TT` para el patrón `2 presenciales + 1 TT` y con TT habilitado.
- Farmacia valida que la persona seleccionada para el primer sábado esté activa.
- Se mantiene la validación de incompatibilidades globales al generar: máximos R/TT y coincidencias MA.
- 59 pruebas automatizadas correctas.

## 2.7.2
- Nueva plantilla `Plantilla_Cuadrantes_Usuarios_v11.xlsx`.
- Nuevo color rosa pastel para fases/orden inicial del año.
- Intensivo: seleccionable de la persona que inicia la primera TT de la cinta.
- Rotatorio: fase inicial F01..F12 por agente.
- EasyVista/Puesto Usuario: orden del primer TT por persona.
- Farmacia: seleccionable de quién trabaja el primer sábado del año.
- Sistemas: inicio individual del ciclo 2 presencial + 1 TT.
- Supervisores: orden TT por subgrupo, respetando límites y prioridad de Guardia.
- Compatibilidad con turnos personalizados y M2 mantenida.
- 46 pruebas automatizadas correctas.

## 2.7.1

- Corrige el desplegable `Turno base` de Intensivo.
- El desplegable toma los códigos de la tabla verde `TURNOS DISPONIBLES / CREADOS`, incluyendo `M`, `M1`, `M2` y nuevos códigos añadidos por el usuario.
- Se confirma `M2 → M1`: M2 conserva su código visible, sigue la lógica de M1 y no hace P en Intensivo.
- La plantilla incorpora una aclaración adicional en `INSTRUCCIONES`.

## 2.7.0

- Nueva plantilla `Plantilla_Cuadrantes_Usuarios_v10.xlsx`.
- Nueva pestaña `INSTRUCCIONES` con ejemplos de usuario.
- Nuevo turno M2, por defecto M2 → M1.
- M2 no hace P en Intensivo.
- Tabla `TURNOS DISPONIBLES / CREADOS` en todos los departamentos.
- Herencia funcional y visual de turnos creados.
- Creación de turnos soportada en Intensivo, Rotatorio, EasyVista, Puesto Usuario, Farmacia, Sistemas y Supervisores.
- Rotatorio integra turnos creados en sufijos D/F y conteo N/D/F.
- GUI y documentación actualizadas.

## 2.6.0

- Corrige el error del ejecutable compilado `No translation file found for domain: 'ES'`.
- `GENERADOR_TURNOS.spec` incorpora `collect_all("holidays")` para empaquetar catálogos y submódulos de `python-holidays`.
- `holidays_provider.py` añade fallback sin `language="es"` si un catálogo no estuviera disponible.
- Nueva plantilla oficial `Plantilla_Cuadrantes_Usuarios_v9.xlsx`.
- Las celdas de reglas/ciclos editables usan un verde más visible (`#C6E0B4`) y textos de ayuda más claros.
- Sin cambios funcionales en los siete calendarios respecto a v2.5.


## 2.5.0

- Plantilla oficial `Plantilla_Cuadrantes_Usuarios_v8.xlsx`.
- Celdas de turnos/ciclos editables marcadas en verde pastel.
- EasyVista y Puesto Usuario leen realmente `CICLO POR SEMANAS`; deja de estar fijado en Python.
- Se admite `TT,TT,TT` y otros ciclos semanales, respetando `Máximo TT por semana`.
- Se pueden crear nuevos turnos base en EasyVista/Puesto Usuario añadiendo una fila de ciclo y asignando el código a PERSONAS.
- Estilo automático para nuevos códigos por familia y leyenda genérica.
- Supervisores: `Ciclo TT (semanas)` editable desde plantilla.
- Corrección de Marian Gutiérrez: el reparto TT evita, cuando es posible, coincidir con su semana de Guardia.
- GUI: nuevo botón `Ayuda para editar turnos`.
- Nuevo `INSTRUCCIONES_TURNOS.md` y `ANALISIS_AJUSTES_V25.md`.
- 31 pruebas automatizadas correctas.

## 2.4.0

### Intensivo · nueva cinta circular

- Nueva plantilla oficial `Plantilla_Cuadrantes_Usuarios_v7.xlsx`.
- Se sustituye el reparto A/B por la cinta visible y editable: `TT,P,TT,TT,M,M,M,M,M,TT,P,TT,M,M,M,M,M,M`.
- La cinta se aplica en el orden vertical de las personas y baja una fila por semana.
- Semana de referencia: lunes 14/12/2026. La rotación continúa entre años.
- La cinta contiene siempre 5 posiciones TT y 2 posiciones P teóricas.
- M1 nunca hace P: una P que cae sobre M1 se convierte en M1 y no se reasigna.
- `Renuncia` mantiene borde magenta y cuenta como posición TT.
- El lector de plantilla valida códigos de cinta, número de posiciones, máximos y separación de las P.

### Resto del programa

- Se mantienen las reglas y formatos validados en v2.3 para Rotatorio, EasyVista, Farmacia, Puesto Usuario, Sistemas y Supervisores.
- Se mantienen cabeceras de subdepartamento horizontales.
- Se mantiene la fila en blanco antes de N/D/F y las agrupaciones B:D, E:G y H:J de Rotatorio.
- Se mantiene la corrección general de `MergedCell object attribute value is read-only`.

### Validación

- 26 pruebas automatizadas correctas.
- Generación de integración verificada para los siete calendarios.

## 2.3.0

### Plantilla / Intensivo

- Nueva `Plantilla_Cuadrantes_Usuarios_v6.xlsx`.
- `Máximo TT en la misma semana` pasa a **5** en Intensivo.
- El patrón A/B con 18 personas queda matemáticamente equilibrado: 90 plazas requeridas y 90 disponibles cada 18 semanas.
- Se mantienen M1 para Ángeles, Vanesa y Carlos; Ángeles sigue como `Renuncia` a TT.

### Formato de salida

- EasyVista, Puesto Usuario, Sistemas y Supervisores: subdepartamentos en orientación horizontal.
- Rotatorio: una fila visible en blanco entre el último agente y N/D/F.
- Rotatorio conserva B:D, E:G y H:J combinadas.
- Se mantiene la protección frente a `MergedCell` de solo lectura.

### Validación

- 22 pruebas automatizadas.
- Generación de integración correcta de los siete calendarios.


## 2.2.0

### Plantilla

- Nueva `Plantilla_Cuadrantes_Usuarios_v5.xlsx`.
- Intensivo: Ángeles Lino Martín, Vanesa Martín y Carlos Centeno configurados como reducción/M1.
- Intensivo: Ángeles Lino Martín configurada como `Renuncia` a TT.
- Rotatorio: Daniel Ameijeiras `Activo=No`; Saraid Lozada `Activo=Sí`.
- Teletrabajo disponible como columna homogénea en todas las tablas; Farmacia queda por defecto en `No`.

### Lógica / Excel

- M1 sigue excluido de P y de su máximo semanal.
- `Renuncia` sigue ocupando plaza TT y se representa con borde magenta.
- Rotatorio vuelve a combinar B:D, E:G y H:J en cada fila activa después de escribir, conservando la alineación con los bloques N/D/F.
- Se mantiene la protección general frente a `MergedCell object attribute value is read-only` en zonas de operadores, Festivos y Leyenda.

### Validación

- Verificada generación real de Rotatorio, EasyVista, Puesto Usuario, Farmacia, Sistemas y Supervisores.
- Intensivo conserva la validación bloqueante de capacidad TT=4 mientras todas las 18 personas participen en el patrón A/B actual.


## 2.1.0

### Plantilla

- Nueva `Plantilla_Cuadrantes_Usuarios_v4.xlsx`.
- Columna `Activo` en todas las tablas de personas.
- Intensivo: Ángeles Lino Martín y Vanesa Martín configuradas como reducción/M1.
- Rotatorio: Daniel Ameijeiras `Activo=No`; Saraid activa. El modelo resultante contiene 12 personas.

### Lógica

- M1 nunca entra en P y no cuenta en el máximo semanal de P.
- `Activo=No` se excluye antes de planificar, por lo que tampoco consume máximos ni fases.
- Se mantiene la validación estricta del máximo TT: la configuración Intensivo de 18 personas TT con patrón A/B y máximo 4 sigue siendo matemáticamente incompatible y se informa como tal.

### Excel

- Corregida la escritura sobre plantillas con celdas combinadas heredadas.
- Corregidas las zonas de operadores, Festivos y resumen N/D/F para evitar `MergedCell object attribute value is read-only`.

## 2.0.0

Reestructuración completa del flujo de configuración.

### GUI

- Se elimina la selección manual de tipo de turno y nombres.
- Nueva selección de `Plantilla_Cuadrantes.xlsx`.
- Validación de pestañas mínimas.
- Botón **Generar plantilla tipo…**.
- Checks dinámicos de calendarios en el orden del Excel.
- Carpeta de salida única.
- Generación secuencial, calendario a calendario.
- Nombres de salida `Calendario_Departamento_Año.xlsx`.

### Plantilla

- Personas y reglas se leen del Excel.
- Leyendas incluidas por calendario.
- Teletrabajo `Sí / Renuncia / No`.
- Renuncia vuelve a contar como plaza TT y se representa en magenta.

### Intensivo

- 8 M/M1 + 1 P configurable mediante `Semanas entre P`.
- Nuevo TT relativo a P con alternancia de patrones A/B.
- Máximo P y TT leído de plantilla.
- Reducción M→M1 y sin P.

### Rotatorio

- Ciclos leídos de la plantilla (`Código × días`).
- N en miércoles; R L-V.
- TT en M/R laborables no festivos.
- N/D/F conserva la regla semana→mes más nuevo.

### Resto

- EasyVista y Puesto Usuario: Base·Base·TT.
- Farmacia: sábados alternos F1/F2.
- Sistemas: patrones TT por persona y separación MA.
- Supervisores: máximos TT por grupo, Renuncia y Guardia tomada de plantilla.

### Salida

- Se incorporan los siete Excel aportados como `templates_tipo/`.
- Se mantiene la apariencia de cada departamento como base de generación.
