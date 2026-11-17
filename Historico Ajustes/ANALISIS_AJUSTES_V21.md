# Análisis de ajustes v2.1

## Intensivo

### M1 / Partido

En el cuadrante Intensivo 2026 más reciente, Ángeles Lino Martín y Vanesa Martín no aparecen en semanas de Partido. La plantilla v4 las marca como reducción, por lo que el motor genera M1 y las excluye de P y del máximo semanal de P.

### Renuncia a Teletrabajo

En el fichero de referencia más reciente `CALENDARIO Turnos Intensivo SACYL 2026.E02(2).xlsx` no se detectan bordes magenta completos: no hay una renuncia TT visible que pueda trasladarse con seguridad a la plantilla.

En una versión anterior del mismo cuadrante (`E02(1)`) sí aparecen bordes magenta para Marcos Alba Rocha, Andrea Durantez, Ángeles Lino Martín, Adrián García Gomez, Héctor Villalba San Jose, Sergio Sánchez Villa y Juan Luis Garcia Herruzo. Como esa versión no coincide exactamente con la plantilla/roster más reciente, v2.1 no convierte automáticamente esos nombres a `Renuncia`; deben confirmarse antes de modificar la plantilla oficial.

### Capacidad TT

M1 sin P corrige la capacidad de Partido, pero no la de TT. El patrón A/B consume 5 plazas TT por persona cada 18 semanas. Con 18 participantes son 90 plazas y un máximo de 4 por semana ofrece 72. Esta incompatibilidad sigue siendo una validación bloqueante.

## Rotatorio

La plantilla contiene 13 nombres históricos, pero Daniel Ameijeiras está de baja y Saraid Lozada Garcia actúa como sustitución. En v4 se conserva Daniel con `Activo=No` y Saraid con `Activo=Sí`, de modo que el calendario real se genera con 12 personas. Con 12 personas el motor encuentra una distribución válida con máximo 2 R.

## Celdas combinadas

Las plantillas visuales originales contienen rangos combinados en zonas que el generador reconstruye. v2.0 intentaba limpiar alguna de esas celdas secundarias y openpyxl devolvía `MergedCell object attribute value is read-only`. v2.1 descombina únicamente las zonas que va a reconstruir (operadores, Festivos y resumen Rotatorio N/D/F) y después vuelve a crear las combinaciones necesarias.
