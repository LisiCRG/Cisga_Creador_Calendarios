# Análisis de ajustes v2.2

## Intensivo

La plantilla oficial marca como reducción/M1 a **Ángeles Lino Martín, Vanesa Martín y Carlos Centeno**. El motor ya excluía M1 de Partido, por lo que estos tres nombres no reciben P ni consumen el máximo de 2 P semanales.

Ángeles figura como **Renuncia a TT**. Cuando su fase teórica sea TT, mantiene M1 presencial, se dibuja borde magenta y cuenta exactamente igual que una plaza TT amarilla.

En el cuadrante Intensivo E02(2) analizado no aparecen otras celdas con borde magenta activas. Por tanto, con la información más reciente no se marca a ningún otro agente como Renuncia.

### Capacidad TT pendiente

La configuración sigue teniendo una incompatibilidad matemática independiente de M1: el patrón A/B consume 5 plazas TT por persona cada 18 semanas. 18 personas activas en TT generan 90 plazas y el máximo 4 permite 72. La v2.2 no altera silenciosamente esa regla y mantiene el error de validación hasta que se cambie el patrón, el máximo o alguna persona pase a `Teletrabajo=No`. `Renuncia` no reduce capacidad porque cuenta dentro del máximo.

## Rotatorio

El listado histórico contiene 13 nombres, pero **Daniel Ameijeiras está de baja** y **Saraid Lozada le sustituye**. La plantilla conserva ambos: Daniel `Activo=No`, Saraid `Activo=Sí`. El modelo efectivo tiene 12 agentes.

### B:D / E:G / H:J

La plantilla visual original combina estas tres zonas en cada fila de agente:

- B:D = DÍAS VAC.
- E:G = DISFRUTADOS
- H:J = PENDIENTES

La v2.1 debía descombinar estas celdas antes de limpiar la fila para evitar `MergedCell`, pero no las restauraba. La v2.2 las vuelve a combinar después de escribir cada agente, de modo que los conteos N/D/F inferiores permanecen alineados con B:J.

## Causa del error MergedCell por departamento

- **EasyVista**: la columna de grupo A está combinada verticalmente entre varias filas de agentes. La limpieza anterior intentaba escribir en las celdas secundarias de esa combinación.
- **Puesto Usuario**: mismo patrón que EasyVista; grupo combinado en A.
- **Sistemas Áreas Especializadas**: varios grupos (Wintel, Linux, BBDD) están combinados verticalmente en A.
- **Supervisores y OPX**: los distintos grupos de supervisión también están combinados verticalmente en A.
- **Farmacia**: no tiene combinaciones de grupo en las filas de agentes; el conflicto provenía de otras zonas heredadas, principalmente la hoja Festivos/estructuras combinadas que el generador reconstruye.
- **Rotatorio**: B:D, E:G y H:J están deliberadamente combinadas en las filas de agentes. Esas combinaciones se deshacen temporalmente para escribir y en v2.2 se restauran.

La estrategia correcta es: **descombinar solo la zona que se va a reconstruir → escribir → recombinar únicamente las combinaciones que forman parte del diseño final**.

## Integración revisada

La v2.2 genera sin error Rotatorio, EasyVista, Puesto Usuario, Farmacia, Sistemas y Supervisores usando sus plantillas tipo. Farmacia incorpora también la columna Teletrabajo de forma homogénea, aunque su regla funcional sigue siendo sin TT.
